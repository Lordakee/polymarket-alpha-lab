"""Linux official-probe preparation proofs; synthetic fixtures only.

No official binary, network, credential or namespace is used or executed here:
every ELF is a locally built stand-in, every identity value is computed from
those synthetic bytes, and the namespace plan is validated as a generated
document. The six official cases are NOT this node's completion condition.
"""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('probe_environment_linux',
                                              ROOT/'scripts/claude_probe_environment.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)


def build_elf(needed=('libc.so.6', 'libgcc_s.so.1'),
              interp='/lib64/ld-linux-x86-64.so.2', *, machine=62, elf_class=2,
              endian=1, e_type=3, magic=b'\x7fELF', ei_version=1,
              include_strtab=True, extra_dynamic=(), body=None, mutate=None):
    """Synthetic x86-64 ELF stand-in; never executed by anything."""
    interp_bytes = interp.encode('ascii') + b'\0' if interp is not None else b''
    phnum, phoff = 3, 64
    interp_off = phoff + 56*phnum
    dyn_off = interp_off + len(interp_bytes)
    dyn_size = 16*(len(needed) + len(extra_dynamic) + (1 if include_strtab else 0) + 1)
    strtab_off = dyn_off + dyn_size
    names, offsets = b'', []
    for soname in needed:
        offsets.append(1 + len(names))
        names += soname.encode('ascii') + b'\0'
    strtab = b'\0' + names
    body = body or b'PAL synthetic ELF stand-in for the official artifact; never executed.\n'*8
    total = strtab_off + len(strtab) + len(body)
    image = bytearray(total)
    image[strtab_off+len(strtab):strtab_off+len(strtab)+len(body)] = body
    ident = bytes(magic[:4]).ljust(4, b'\0') + bytes([elf_class, endian, ei_version, 0]) + b'\0'*8
    image[:16] = ident
    struct.pack_into('<HHIQQQIHHHHHH', image, 16, e_type, machine, 1, 0, phoff, 0, 0,
                     64, 56, phnum, 64, 0, 0)
    interp_header = (struct.pack('<IIQQQQQQ', 3, 4, interp_off, interp_off, 0,
                                 len(interp_bytes), len(interp_bytes), 0x10)
                     if interp is not None else struct.pack('<IIQQQQQQ', *([0]*8)))
    image[phoff:phoff+56*phnum] = b''.join((
        struct.pack('<IIQQQQQQ', 1, 5, 0, 0, 0, total, total, 0x1000),
        interp_header,
        struct.pack('<IIQQQQQQ', 2, 6, dyn_off, dyn_off, 0, dyn_size, dyn_size, 8)))
    image[interp_off:interp_off+len(interp_bytes)] = interp_bytes
    dynamic = b''.join(struct.pack('<QQ', 1, offset) for offset in offsets)
    dynamic += b''.join(struct.pack('<QQ', tag, value) for tag, value in extra_dynamic)
    if include_strtab:
        dynamic += struct.pack('<QQ', 5, strtab_off)
    dynamic += struct.pack('<QQ', 0, 0)
    image[dyn_off:dyn_off+len(dynamic)] = dynamic
    image[strtab_off:strtab_off+len(strtab)] = strtab
    if mutate is not None:
        mutate(image, dict(phoff=phoff, interp_off=interp_off, dyn_off=dyn_off,
                           strtab_off=strtab_off, strtab_len=len(strtab), total=total))
    return bytes(image)


ELF = build_elf()


def valid_linux_manifest(data=ELF):
    return dict(schema='claude-probe-image-linux-v1', path='claude',
                sha256=sha256(data).hexdigest(), bytes=len(data),
                version='2.1.278', platform='linux-x86_64')


def write_linux_image(parent, name='image', *, data=None, value=None, raw=None,
                      inventory=(), skip_member=False):
    data = ELF if data is None else data
    if value is None and raw is None:
        value = valid_linux_manifest(data)
    image = parent/name; image.mkdir()
    if not skip_member:
        (image/'claude').write_bytes(data)
    (image/'image-manifest.json').write_text(
        json.dumps(value) if raw is None else raw, encoding='utf-8')
    for extra in inventory:
        (image/extra).write_bytes(b'unexpected')
    return image


def linux_payload(parent, name='payload', complete=True):
    root = parent/name; root.mkdir()
    (root/'source').mkdir(); (root/'source/synthetic.py').write_bytes(b'# synthetic source\n')
    (root/'source/src').mkdir(); (root/'source/src/pkg.py').write_bytes(b'# package code\n')
    (root/'source/tests').mkdir()
    (root/'source/tests/test_research_claude_profile_native.py').write_bytes(b'# native stand-in\n')
    if complete:
        (root/'python/lib/python3.12/site-packages').mkdir(parents=True)
        (root/'python/lib/python3.12/site-packages/pytest-stub.py').write_bytes(b'# pytest stand-in\n')
        (root/'python/bin').mkdir(parents=True)
        (root/'python/bin/python3').write_bytes(b'#!/bin/sh\nsynthetic bundled python; never executed\n')
    m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
    (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    return root, m


def linux_setup(tmp_path):
    root, _ = linux_payload(tmp_path)
    image = write_linux_image(tmp_path)
    control = tmp_path/'control'
    e._official_control_generate(image, control, 'linux')
    return root, image, control


def image_snapshot(image):
    return {p.name: p.read_bytes() for p in image.iterdir()}


LINUX_PROBE_VARS = (
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE', '1'),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE', '/pal-claude-image/claude'),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256', sha256(ELF).hexdigest()),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES', str(len(ELF))),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST', '1'),
)


# --- Artifact identity: owner-measured parameters, never invented ----------

def test_linux_identity_is_owner_supplied_and_never_invented():
    # No module constant pins a Linux digest or byte size; identity enters only
    # through the operator-authored image manifest.
    embedded = [name for name, value in vars(e).items()
                if type(value) is str and re.fullmatch('[0-9a-f]{64}', value)]
    assert embedded == []
    assert not hasattr(e, 'LINUX_IMAGE_SHA256') and not hasattr(e, 'LINUX_IMAGE_BYTES')
    assert b'{image_sha256}' in e.LINUX_LAUNCHER_TEMPLATE
    assert b'{image_bytes}' in e.LINUX_LAUNCHER_TEMPLATE
    source = (ROOT/'scripts/claude_probe_environment.py').read_text(encoding='utf-8')
    assert 'LINUX_IMAGE_SHA256' not in source and 'LINUX_IMAGE_BYTES' not in source


def test_linux_identity_and_closure_derived_from_image_bytes(tmp_path):
    elf = build_elf(needed=('libz.so.1', 'libc.so.6', 'libc.so.6'))
    image = write_linux_image(tmp_path, data=elf)
    value, facts = e._load_official_image(image, 'linux')
    assert value == valid_linux_manifest(elf)
    assert facts == {'interp': '/lib64/ld-linux-x86-64.so.2',
                     'needed': ['libc.so.6', 'libz.so.1']}
    assert value['version'] == e.OFFICIAL_IMAGE_VERSION == '2.1.278'


@pytest.mark.parametrize('override,expected', [
    (dict(machine=40), 'image_arch_unsupported'),
    (dict(machine=183), 'image_arch_unsupported'),
    (dict(elf_class=1), 'image_arch_unsupported'),
    (dict(endian=2), 'image_arch_unsupported'),
    (dict(e_type=1), 'image_elf_invalid'),
    (dict(magic=b'MZ\x90\0'), 'image_elf_invalid'),
    (dict(ei_version=0), 'image_elf_invalid'),
])
def test_linux_rejects_wrong_architecture_or_elf_structure(tmp_path, override, expected):
    image = write_linux_image(tmp_path, data=build_elf(**override))
    with pytest.raises(ValueError, match=expected):
        e._load_official_image(image, 'linux')


@pytest.mark.parametrize('fault', ['strtab-overrun', 'needed-no-strtab',
                                   'missing-interp', 'soname-no-nul',
                                   'soname-control-char', 'phoff-past-end',
                                   'truncated-header', 'interp-relative'])
def test_linux_elf_parsing_is_bounded_and_fail_closed(tmp_path, fault):
    if fault == 'strtab-overrun':
        data = build_elf(extra_dynamic=((1, 999999),))
    elif fault == 'needed-no-strtab':
        data = build_elf(include_strtab=False)
    elif fault == 'missing-interp':
        data = build_elf(interp=None)
    elif fault == 'soname-no-nul':
        def strip(image, layout):
            image[layout['strtab_off']+layout['strtab_len']-1] = ord('x')
        data = build_elf(needed=('deadend',), mutate=strip)
    elif fault == 'soname-control-char':
        data = build_elf(needed=('bad\x01name',))
    elif fault == 'phoff-past-end':
        def move(image, layout):
            struct.pack_into('<Q', image, 32, 10**7)
        data = build_elf(mutate=move)
    elif fault == 'truncated-header':
        data = build_elf()[:20]
    else:
        data = build_elf(interp='lib64/ld-linux-x86-64.so.2')
    image = write_linux_image(tmp_path, data=data)
    with pytest.raises(ValueError, match='image_elf_invalid'):
        e._load_official_image(image, 'linux')


def test_linux_elf_streaming_digest_keeps_separate_bound(tmp_path, monkeypatch):
    elf = build_elf(body=b'PAL bounded synthetic payload; never executed.\n'*256)
    image = write_linux_image(tmp_path, data=elf)
    monkeypatch.setattr(e, 'OFFICIAL_IMAGE_CHUNK', 16)
    monkeypatch.setattr(e, 'MAX_FILE', 4096)
    value, facts = e._load_official_image(image, 'linux')
    assert value['bytes'] == len(elf) > 4096
    assert facts['needed'] == ['libc.so.6', 'libgcc_s.so.1']


@pytest.mark.parametrize('fault', ['malformed', 'duplicate-key', 'nonfinite',
    'wrong-root', 'wrong-schema', 'missing-platform', 'extra-key', 'wrong-path',
    'wrong-version', 'wrong-platform', 'digest-uppercase', 'digest-short',
    'digest-integer', 'bytes-bool', 'bytes-zero', 'bytes-negative',
    'bytes-float', 'bytes-oversize', 'nonascii', 'manifest-oversize'])
def test_linux_manifest_protocol_rejections(tmp_path, fault):
    manifest = valid_linux_manifest()
    raw = None
    if fault == 'malformed':
        raw = '{ not json'
    elif fault == 'duplicate-key':
        raw = json.dumps(manifest).replace('"path":', '"path":"claude","path":', 1)
    elif fault == 'nonfinite':
        raw = json.dumps(manifest).replace(str(manifest['bytes']), 'NaN', 1)
    elif fault == 'wrong-root':
        raw = '[1,2]'
    elif fault == 'nonascii':
        raw = json.dumps(manifest).replace('2.1.278', '2.1.27\u8e0f', 1)
    elif fault == 'manifest-oversize':
        manifest['padding'] = 'x'*5000
    else:
        manifest = {'wrong-schema': dict(manifest, schema='claude-probe-image-v1'),
                    'missing-platform': {k: v for k, v in manifest.items() if k != 'platform'},
                    'extra-key': dict(manifest, extra=1),
                    'wrong-path': dict(manifest, path='claude.exe'),
                    'wrong-version': dict(manifest, version='2.1.277'),
                    'wrong-platform': dict(manifest, platform='linux-aarch64'),
                    'digest-uppercase': dict(manifest, sha256=manifest['sha256'].upper()),
                    'digest-short': dict(manifest, sha256='a'*63),
                    'digest-integer': dict(manifest, sha256=12345),
                    'bytes-bool': dict(manifest, bytes=True),
                    'bytes-zero': dict(manifest, bytes=0),
                    'bytes-negative': dict(manifest, bytes=-1),
                    'bytes-float': dict(manifest, bytes=float(manifest['bytes'])),
                    'bytes-oversize': dict(manifest, bytes=536870913)}[fault]
    image = write_linux_image(tmp_path, value=manifest, raw=raw)
    with pytest.raises(ValueError):
        e._load_official_image(image, 'linux')


@pytest.mark.parametrize('fault', ['missing-member', 'empty', 'extra-file',
                                   'case-variant', 'manifest-absent'])
def test_linux_image_rejects_unexpected_inventory(tmp_path, fault):
    if fault == 'missing-member':
        image = write_linux_image(tmp_path, skip_member=True)
    elif fault == 'empty':
        image = tmp_path/'image'; image.mkdir()
    elif fault == 'case-variant':
        image = tmp_path/'image'; image.mkdir()
        (image/'Claude').write_bytes(ELF)
        (image/'image-manifest.json').write_text(json.dumps(valid_linux_manifest()), encoding='utf-8')
    elif fault == 'manifest-absent':
        image = tmp_path/'image'; image.mkdir()
        (image/'claude').write_bytes(ELF)
    else:
        image = write_linux_image(tmp_path, inventory=('notes.txt',))
    with pytest.raises(ValueError):
        e._load_official_image(image, 'linux')


def test_linux_content_mismatch_and_change_reuse_protocol(tmp_path):
    image = write_linux_image(tmp_path, value=dict(valid_linux_manifest(), sha256='0'*64))
    with pytest.raises(ValueError, match='image_hash_mismatch'):
        e._load_official_image(image, 'linux')
    image2 = write_linux_image(tmp_path, 'image2')
    with (image2/'claude').open('ab') as stream:
        stream.write(b'grown')
    with pytest.raises(ValueError, match='image_size_mismatch'):
        e._load_official_image(image2, 'linux')


# --- Launcher companion -----------------------------------------------------

def test_linux_launcher_exact_contract():
    data = e.official_launcher(valid_linux_manifest(), platform='linux')
    text = data.decode('ascii')
    assert data.startswith(b'#!/bin/sh\n')
    assert b'\r' not in data and b'\xef\xbb\xbf' not in data[:3]
    assert b'{image_sha256}' not in data and b'{image_bytes}' not in data
    lines = text.split('\n')
    assert lines[1] == 'set -eu'
    assert lines[2] == 'if [ "${1-}" != "--isolated-host-attested" ]; then exit 2; fi'
    assert lines[3] == 'if [ "$#" -ne 1 ]; then exit 2; fi'
    assert 'cd /pal-output || exit 2' in text
    for name, value in LINUX_PROBE_VARS:
        assert f'export {name}={value}' in text
    assert 'export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1' in text
    assert 'unset PYTEST_ADDOPTS PYTEST_PLUGINS' in text
    assert 'export TMPDIR=/pal-output/launcher-tmp' in text
    exec_index = next(i for i, line in enumerate(lines)
                      if line.startswith('exec /pal-input/python/bin/python3 -I -S -B -c '))
    guard_region = '\n'.join(lines[:exec_index])
    assert 'for name in launcher-tmp pytest-tmp pytest.log junit.xml exit-code.txt; do' in guard_region
    assert 'if [ -e "/pal-output/$name" ]; then exit 2; fi' in guard_region
    assert 'mkdir /pal-output/launcher-tmp || exit 2' in guard_region
    exec_line = lines[exec_index]
    for fragment in ("sys.path[:0]=['/pal-input/source','/pal-input/source/src',",
                     "'/pal-input/python/lib/python3.12/site-packages']",
                     "'--basetemp=/pal-output/pytest-tmp'",
                     "'--junitxml=/pal-output/junit.xml'",
                     "'/pal-input/source/tests/test_research_claude_profile_native.py'",
                     "receipt=open('/pal-output/exit-code.txt','x',encoding='ascii')",
                     "raise SystemExit(code)"):
        assert fragment in exec_line
    assert exec_line.endswith('> /pal-output/pytest.log 2>&1')
    assert max(len(line) for line in lines) < 4096
    assert 'HTTP_PROXY' not in text and 'HTTPS_PROXY' not in text and 'HOME=' not in text


@pytest.mark.parametrize('fault', [{'sha256': 'A'*64}, {'sha256': 'a'*63},
                                   {'sha256': 12345}, {'bytes': True}, {'bytes': 0},
                                   {'bytes': -1}, {'bytes': 1.5},
                                   {'bytes': 536870913}])
def test_linux_launcher_refuses_manifest_faults(fault):
    with pytest.raises(ValueError):
        e.official_launcher({**valid_linux_manifest(), **fault}, platform='linux')


@pytest.mark.parametrize('mode,ok', [(0o755, True), (0o644, False), (0o777, False),
                                     (0o700, False), (0o745, False), (0o4755, False),
                                     (0o2755, False), (0o1755, False), (0o000, False)])
def test_linux_launcher_mode_rule_is_exact_0755(mode, ok):
    problem = e._linux_launcher_mode_problem(mode)
    assert (problem is None) is ok
    if not ok:
        assert problem == 'launcher_mode_invalid'


def test_linux_control_mode_check_is_wired(tmp_path, monkeypatch):
    root, image, control = linux_setup(tmp_path)
    monkeypatch.setattr(e, '_LINUX_MODE_MEANINGFUL', True)
    monkeypatch.setattr(e.stat, 'S_IMODE', lambda mode: 0o644)
    with pytest.raises(ValueError, match='launcher_mode_invalid'):
        e._official_config_generate(root, image, control, tmp_path/'out',
                                    tmp_path/'plan.json', 'linux')
    assert not (tmp_path/'out').exists() and not (tmp_path/'plan.json').exists()


def test_linux_official_control_generates_launcher_with_posix_mode(tmp_path, monkeypatch):
    image = write_linux_image(tmp_path)
    calls = []
    real_chmod = os.chmod
    def recording(path, mode):
        calls.append((Path(path).name, mode))
        return real_chmod(path, mode)
    monkeypatch.setattr(e.os, 'chmod', recording)
    monkeypatch.setattr(e, '_LINUX_MODE_MEANINGFUL', True)
    control = tmp_path/'control'
    result = e._official_control_generate(image, control, 'linux')
    assert result['status'] == 'official_control_generated_not_launched'
    assert result['image_platform'] == 'linux-x86_64'
    assert result['runtime_interp'] == '/lib64/ld-linux-x86-64.so.2'
    assert result['runtime_needed'] == ['libc.so.6', 'libgcc_s.so.1']
    assert result['official_cli_executed'] is False and result['activation_authorized'] is False
    assert sorted(os.listdir(control)) == ['official-probe.sh']
    assert calls == [('official-probe.sh', 0o755)]
    assert (control/'official-probe.sh').read_bytes() == e.official_launcher(
        valid_linux_manifest(), platform='linux')


@pytest.mark.parametrize('fault', ['missing', 'empty-file', 'edited', 'additional',
                                   'renamed', 'replaced-by-dir'])
def test_linux_control_requires_exact_generated_contents(tmp_path, fault):
    root, image, control = linux_setup(tmp_path)
    launcher = control/'official-probe.sh'
    if fault == 'missing':
        launcher.unlink()
    elif fault == 'empty-file':
        launcher.write_bytes(b'')
    elif fault == 'edited':
        launcher.write_bytes(e.official_launcher(valid_linux_manifest(), platform='linux') + b'# edited\n')
    elif fault == 'additional':
        (control/'extra.sh').write_bytes(b'x')
    elif fault == 'renamed':
        launcher.rename(control/'other.sh')
    else:
        launcher.unlink(); launcher.mkdir()
    before = image_snapshot(image)
    with pytest.raises(ValueError):
        e._official_config_generate(root, image, control, tmp_path/'out',
                                    tmp_path/'plan.json', 'linux')
    assert not (tmp_path/'out').exists() and not (tmp_path/'plan.json').exists()
    assert image_snapshot(image) == before


@pytest.mark.parametrize('kind,expected', [('output-dir', 'output_dir_exists'),
                                           ('destination-file', 'destination_exists')])
def test_linux_config_rejects_existing_targets(tmp_path, kind, expected):
    root, image, control = linux_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.json'
    if kind == 'output-dir':
        output.mkdir(); (output/'kept').write_bytes(b'marker')
    else:
        destination.write_bytes(b'marker')
    with pytest.raises(ValueError, match=expected):
        e._official_config_generate(root, image, control, output, destination, 'linux')
    if kind == 'output-dir':
        assert (output/'kept').read_bytes() == b'marker'
    else:
        assert destination.read_bytes() == b'marker'


@pytest.mark.parametrize('fault', ['corrupt', 'layout-missing', 'windows-layout'])
def test_linux_config_payload_verification_failure_creates_nothing(tmp_path, fault):
    if fault == 'windows-layout':
        root = tmp_path/'payload'; root.mkdir()
        (root/'source').mkdir(); (root/'source/synthetic.py').write_bytes(b'# synthetic source\n')
        (root/'source/src').mkdir(); (root/'source/src/pkg.py').write_bytes(b'# package code\n')
        (root/'source/tests').mkdir()
        (root/'source/tests/test_research_claude_profile_native.py').write_bytes(b'# native stand-in\n')
        (root/'python/Lib/site-packages').mkdir(parents=True)
        (root/'python/Lib/site-packages/pytest-stub.py').write_bytes(b'# pytest stand-in\n')
        (root/'python/python.exe').write_bytes(b'MZ synthetic bundled python; never executed\n')
        m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
        (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    else:
        root, _ = linux_payload(tmp_path, complete=fault != 'layout-missing')
        if fault == 'corrupt':
            (root/'source/synthetic.py').write_bytes(b'changed')
    image = write_linux_image(tmp_path); control = tmp_path/'control'
    e._official_control_generate(image, control, 'linux')
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.json'
    with pytest.raises(ValueError, match='payload_layout_unsupported|content_mismatch'):
        e._official_config_generate(root, image, control, output, destination, 'linux')
    assert not output.exists() and not destination.exists()
    assert (control/'official-probe.sh').is_file()


@pytest.mark.parametrize('kind,expected', [('equal', 'destination_exists'),
                                           ('nested', 'mapping_overlap'),
                                           ('ancestor', 'destination_exists')])
def test_linux_control_rejects_image_overlap_before_creation(tmp_path, kind, expected):
    image = write_linux_image(tmp_path)
    untouched = image_snapshot(image)
    if kind == 'equal':
        destination = image
    elif kind == 'nested':
        destination = image/'nested-control'
    else:
        destination = tmp_path
    with pytest.raises(ValueError, match=expected):
        e._official_control_generate(image, destination, 'linux')
    assert image_snapshot(image) == untouched
    if kind == 'nested':
        assert not destination.exists()


# --- Namespace plan: synthetic namespace/networking/cleanup proofs ---------

def test_linux_official_config_writes_reviewed_namespace_plan(tmp_path):
    root, image, control = linux_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.json'
    result = e._official_config_generate(root, image, control, output, destination, 'linux')
    assert result['status'] == 'official_config_generated_not_launched'
    assert result['namespaces'] == list(e.LINUX_NAMESPACES)
    assert result['runtime_needed'] == ['libc.so.6', 'libgcc_s.so.1']
    assert result['official_cli_executed'] is False and result['activation_authorized'] is False
    assert list(output.iterdir()) == []
    raw = destination.read_bytes()
    assert all(byte < 128 for byte in raw)
    plan = json.loads(raw)
    assert plan['schema'] == 'claude-probe-namespace-linux-v1'
    assert plan['generation'] == 'config_only_not_executed'
    assert sorted(plan['namespaces']) == sorted(e.LINUX_NAMESPACES)
    assert plan['network'] == {'mode': 'loopback_only',
                               'external_egress': 'unavailable', 'address': '127.0.0.1'}
    mounts = {m['role']: m for m in plan['mounts']}
    assert [m['role'] for m in plan['mounts']] == ['INPUT', 'IMAGE', 'CONTROL', 'OUTPUT', 'SCRATCH']
    assert [m['readonly'] for m in plan['mounts']] == [True, True, True, False, False]
    assert mounts['INPUT'] == {'role': 'INPUT', 'host': str(root), 'guest': '/pal-input',
                               'readonly': True, 'kind': 'bind'}
    assert mounts['OUTPUT']['host'] == str(output) and mounts['OUTPUT']['guest'] == '/pal-output'
    assert mounts['SCRATCH'] == {'role': 'SCRATCH', 'host': None, 'guest': '/pal-scratch',
                                 'readonly': False, 'kind': 'tmpfs',
                                 'size_limit_bytes': e.LINUX_SCRATCH_BYTES}
    argv = plan['argv']
    assert argv[0] == 'bwrap'
    for flag in ('--unshare-user', '--unshare-ipc', '--unshare-pid', '--unshare-net',
                 '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
                 '--dev', '/dev', '--proc', '/proc', '--cap-drop', 'ALL'):
        assert argv.count(flag) == 1, flag
    for pair in (('--dev', '/dev'), ('--proc', '/proc')):
        index = argv.index(pair[0])
        assert tuple(argv[index:index+2]) == pair
    for sequence in (('--tmpfs', e.LINUX_GUESTS['scratch'], '--sizelimit',
                      str(e.LINUX_SCRATCH_BYTES)),
                     ('--tmpfs', '/tmp', '--sizelimit', str(e.LINUX_TMP_BYTES))):
        index = argv.index(sequence[1])
        assert tuple(argv[index-1:index+3]) == sequence
    assert argv.count('--ro-bind') == 3 and argv.count('--bind') == 1
    ro_hosts = {argv[i+1] for i in range(len(argv)-2) if argv[i] == '--ro-bind'}
    rw_hosts = {argv[i+1] for i in range(len(argv)-2) if argv[i] == '--bind'}
    assert ro_hosts == {str(root), str(image), str(control)}
    assert rw_hosts == {str(output)}
    assert argv[-3:] == ['/bin/sh', '-c',
                         'ip link set lo up && exec /pal-control/official-probe.sh'
                         ' --isolated-host-attested']
    assert plan['child_environment'] == {'PATH': '/usr/bin:/bin'}
    assert sorted(plan['excluded_host_surfaces']) == sorted(e.LINUX_EXCLUDED_SURFACES)
    assert plan['bounds'] == {'memory_mb': 4096,
                              'cgroup_controls': 'require_qualification_before_run'}
    assert plan['image']['runtime_needed'] == ['libc.so.6', 'libgcc_s.so.1']
    assert plan['image']['runtime_interp'] == '/lib64/ld-linux-x86-64.so.2'
    assert plan['image']['closure_derived_from'] == 'image_bytes'
    assert plan['official_cli_executed'] is False and plan['activation_authorized'] is False
    assert e._linux_namespace_plan_problem(plan) is None
    # Deterministic regeneration from unchanged inputs yields identical bytes.
    import shutil
    shutil.rmtree(output); destination.unlink()
    e._official_config_generate(root, image, control, output, destination, 'linux')
    assert destination.read_bytes() == raw


@pytest.mark.parametrize('mutation', [
    'schema', 'generation', 'drop-namespace', 'extra-namespace', 'network-shared',
    'network-egress', 'writable-input', 'writable-image', 'guest-swap',
    'no-die-with-parent', 'no-new-session', 'no-clearenv', 'cap-drop-partial',
    'bind-image-writable', 'argv-prefix', 'inner-no-loopback', 'inner-no-attest',
    'child-env-home', 'excluded-empty', 'bounds-memory', 'bounds-cgroup',
    'executed-true', 'authorized-true', 'closure-interp-relative',
    'closure-unsorted', 'closure-invented-member', 'mounts-count',
    'scratch-size', 'tmpfs-count', 'no-proc', 'unknown-flag-dev-bind',
    'unknown-flag-bind-try', 'unknown-flag-ro-bind-try', 'dev-proc-swap',
    'sizelimit-scratch-drop', 'sizelimit-scratch-inflate', 'sizelimit-tmp-drop',
    'sizelimit-tmp-inflate', 'tmpfs-operand-drop'])
def test_linux_namespace_plan_self_check_rejects_tampering(tmp_path, mutation):
    root, image, control = linux_setup(tmp_path)
    value, facts = e._load_official_image(image, 'linux')
    plan = e._linux_namespace_plan(root, image, control, tmp_path/'out', value, facts)
    if mutation == 'schema':
        plan['schema'] = 'other'
    elif mutation == 'generation':
        plan['generation'] = 'executed'
    elif mutation == 'drop-namespace':
        plan['namespaces'].remove('pid')
    elif mutation == 'extra-namespace':
        plan['namespaces'].append('cgroup')
    elif mutation == 'network-shared':
        plan['network']['mode'] = 'shared'
    elif mutation == 'network-egress':
        plan['network']['external_egress'] = 'available'
    elif mutation in ('writable-input', 'writable-image'):
        plan['mounts'][0 if mutation == 'writable-input' else 1]['readonly'] = False
    elif mutation == 'guest-swap':
        plan['mounts'][0]['guest'], plan['mounts'][3]['guest'] = \
            plan['mounts'][3]['guest'], plan['mounts'][0]['guest']
    elif mutation in ('no-die-with-parent', 'no-new-session', 'no-clearenv'):
        plan['argv'].remove('--'+mutation.removeprefix('no-'))
    elif mutation == 'cap-drop-partial':
        index = plan['argv'].index('--cap-drop')
        plan['argv'][index+1] = 'NET_RAW'
    elif mutation == 'bind-image-writable':
        index = next(i for i in range(len(plan['argv'])-2)
                     if plan['argv'][i] == '--ro-bind' and plan['argv'][i+1] == str(image))
        plan['argv'][index] = '--bind'
    elif mutation == 'argv-prefix':
        plan['argv'][0] = 'docker'
    elif mutation == 'inner-no-loopback':
        plan['argv'][-1] = 'exec /pal-control/official-probe.sh --isolated-host-attested'
    elif mutation == 'inner-no-attest':
        plan['argv'][-1] = 'ip link set lo up && exec /pal-control/official-probe.sh'
    elif mutation == 'child-env-home':
        plan['child_environment'] = {'PATH': '/usr/bin:/bin', 'HOME': '/root'}
    elif mutation == 'excluded-empty':
        plan['excluded_host_surfaces'] = []
    elif mutation == 'bounds-memory':
        plan['bounds']['memory_mb'] = 8192
    elif mutation == 'bounds-cgroup':
        plan['bounds']['cgroup_controls'] = 'qualified'
    elif mutation == 'executed-true':
        plan['official_cli_executed'] = True
    elif mutation == 'authorized-true':
        plan['activation_authorized'] = True
    elif mutation == 'closure-interp-relative':
        plan['image']['runtime_interp'] = 'lib64/ld-linux-x86-64.so.2'
    elif mutation == 'closure-unsorted':
        plan['image']['runtime_needed'] = ['z.so', 'a.so']
    elif mutation == 'closure-invented-member':
        plan['image']['member'] = 'claude.exe'
    elif mutation == 'mounts-count':
        plan['mounts'].pop()
    elif mutation == 'scratch-size':
        plan['mounts'][4]['size_limit_bytes'] = 0
    elif mutation == 'tmpfs-count':
        index = plan['argv'].index('/tmp')
        plan['argv'].remove('/tmp')
    elif mutation == 'unknown-flag-dev-bind':
        index = plan['argv'].index('--ro-bind')
        plan['argv'][index:index] = ['--dev-bind', '/etc']
    elif mutation in ('unknown-flag-bind-try', 'unknown-flag-ro-bind-try'):
        plan['argv'].append('--'+mutation.removeprefix('unknown-flag-'))
    elif mutation == 'dev-proc-swap':
        dev_index = plan['argv'].index('--dev')
        proc_index = plan['argv'].index('--proc')
        plan['argv'][dev_index+1] = '/proc'
        plan['argv'][proc_index+1] = '/dev'
    elif mutation in ('sizelimit-scratch-drop', 'sizelimit-scratch-inflate'):
        index = plan['argv'].index(e.LINUX_GUESTS['scratch'])
        if mutation.endswith('drop'):
            del plan['argv'][index+1:index+3]
        else:
            plan['argv'][index+2] = '999'
    elif mutation in ('sizelimit-tmp-drop', 'sizelimit-tmp-inflate'):
        index = plan['argv'].index('/tmp')
        if mutation.endswith('drop'):
            del plan['argv'][index+1:index+3]
        else:
            plan['argv'][index+2] = '999'
    elif mutation == 'tmpfs-operand-drop':
        plan['argv'].remove(e.LINUX_GUESTS['scratch'])
    else:
        plan['argv'].remove('--proc')
    assert e._linux_namespace_plan_problem(plan) == 'namespace_plan_invalid'


# --- Generation boundary: no processes, no silent writes --------------------

def test_linux_generation_never_starts_processes(monkeypatch, tmp_path):
    def launched(*args, **kwargs):
        pytest.fail('process launched')
    monkeypatch.setattr(subprocess, 'run', launched)
    monkeypatch.setattr(subprocess, 'check_output', launched)
    monkeypatch.setattr(subprocess, 'Popen', launched)
    monkeypatch.setattr(os, 'system', launched, raising=False)
    monkeypatch.setattr(os, 'startfile', launched, raising=False)
    root, image, control = linux_setup(tmp_path)
    assert e._official_control_generate(image, tmp_path/'control2', 'linux')[
        'official_cli_executed'] is False
    assert e._official_config_generate(root, image, control, tmp_path/'output2',
                                       tmp_path/'plan2.json', 'linux')[
        'activation_authorized'] is False
    assert (tmp_path/'control2/official-probe.sh').is_file()
    assert (tmp_path/'plan2.json').is_file() and list((tmp_path/'output2').iterdir()) == []


def test_linux_generation_preserves_preparation_inputs(tmp_path):
    root, m = linux_payload(tmp_path)
    before = {p.relative_to(root).as_posix(): p.read_bytes()
              for p in root.rglob('*') if p.is_file()}
    image = write_linux_image(tmp_path)
    untouched = image_snapshot(image)
    control = tmp_path/'control'
    e._official_control_generate(image, control, 'linux')
    e._official_config_generate(root, image, control, tmp_path/'out',
                                tmp_path/'plan.json', 'linux')
    after = {p.relative_to(root).as_posix(): p.read_bytes()
             for p in root.rglob('*') if p.is_file()}
    assert after == before
    assert e.verify(root) == m
    assert image_snapshot(image) == untouched
    assert (control/'official-probe.sh').read_bytes() == e.official_launcher(
        e._load_official_image(image, 'linux')[0], platform='linux')


def test_linux_partial_io_failure_preserves_attempt(tmp_path, monkeypatch):
    import shutil
    image = write_linux_image(tmp_path)
    control = tmp_path/'control'
    real = e._linux_exclusive_write
    def failing(path, data, mode):
        if path.name == 'official-probe.sh':
            raise OSError('synthetic linux launcher write failure')
        return real(path, data, mode)
    monkeypatch.setattr(e, '_linux_exclusive_write', failing)
    with pytest.raises(OSError):
        e._official_control_generate(image, control, 'linux')
    assert control.is_dir() and list(control.iterdir()) == []
    monkeypatch.undo()
    shutil.rmtree(control)
    e._official_control_generate(image, control, 'linux')
    root, _ = linux_payload(tmp_path)
    output = tmp_path/'official-output'; plan = tmp_path/'official-probe.json'
    real_write = e._exclusive_write
    def failing_plan(path, data):
        if path == plan:
            raise OSError('synthetic plan write failure')
        return real_write(path, data)
    monkeypatch.setattr(e, '_exclusive_write', failing_plan)
    with pytest.raises(OSError):
        e._official_config_generate(root, image, control, output, plan, 'linux')
    assert output.is_dir() and list(output.iterdir()) == [] and not plan.exists()
    monkeypatch.undo()
    with pytest.raises(ValueError, match='output_dir_exists'):
        e._official_config_generate(root, image, control, output, plan, 'linux')


# --- Platform selection and CLI surface -------------------------------------

def test_linux_platform_token_rules():
    assert e._official_platform(None) is None
    assert e._official_platform('windows') == 'windows'
    assert e._official_platform('linux') == 'linux'
    for bad in ('darwin', '', 'Linux', 1, b'linux'):
        with pytest.raises(ValueError, match='official_platform_unsupported'):
            e._official_platform(bad)


def test_linux_path_argument_lexical_rules():
    for bad in ('', 'relative', 'C:/pal', r'\\server\share', '/a/../b', '/a/./b',
                '/a//b', '/a/', '/a%b', '/a\x00b', '/a\rb', '/a\x7fb', 'x'*5000):
        with pytest.raises(ValueError, match='official_path_invalid'):
            e._official_path_argument(bad, platform='linux')
    accepted = e._official_path_argument('/opt/pal/input', platform='linux')
    assert str(accepted) == os.sep.join(('/opt/pal/input'.split('/')))
    with pytest.raises(ValueError, match='destination_suffix_invalid'):
        e._official_path_argument('/opt/pal/probe.wsb', file=True, platform='linux')
    assert e._official_path_argument('/opt/pal/probe.json', file=True,
                                     platform='linux').name == 'probe.json'


def test_linux_cli_platform_flag(monkeypatch, capsys, tmp_path):
    image = write_linux_image(tmp_path)
    def cli(*args):
        monkeypatch.setattr(sys, 'argv', ['probe', *args])
        return e.main()
    assert cli('official-config', '--payload-root', str(tmp_path/'p'),
               '--image-dir', str(image), '--control-dir', str(tmp_path/'c'),
               '--output-dir', str(tmp_path/'o'), '--destination', str(tmp_path/'x.json'),
               '--platform', 'linux') == 1
    assert json.loads(capsys.readouterr().out)['reason'] == 'isolated_host_attestation_required'
    with pytest.raises(SystemExit) as caught:
        cli('official-control', '--image-dir', str(image),
            '--destination', str(tmp_path/'c'), '--platform', 'darwin')
    assert caught.value.code == 2
    # Host-spelled non-posix paths are refused by the linux flavor before access.
    if os.name == 'nt':
        assert cli('official-control', '--image-dir', str(image),
                   '--destination', str(tmp_path/'c2'), '--platform', 'linux') == 1
        assert json.loads(capsys.readouterr().out)['reason'] == 'official_path_invalid'
        assert not (tmp_path/'c2').exists()


def test_windows_flavor_stays_frozen_next_to_linux(tmp_path):
    from tests import test_claude_probe_environment as windows_tests
    assert windows_tests.e is not e
    assert e.OFFICIAL_LAUNCHER_TEMPLATE.startswith(b'@echo off\r\n')
    assert e.LINUX_LAUNCHER_TEMPLATE.startswith(b'#!/bin/sh\n')
    assert e.OFFICIAL_IMAGE_KEYS == {'schema', 'path', 'sha256', 'bytes', 'version'}
    assert e.LINUX_IMAGE_KEYS == e.OFFICIAL_IMAGE_KEYS | {'platform'}
    # The frozen windows entry point still verifies the historical fixture.
    assert windows_tests.official_payload  # shared fixture surface remains importable
