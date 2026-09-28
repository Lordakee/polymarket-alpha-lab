"""Linux official-probe preparation proofs; synthetic fixtures only.

No official binary, network, credential or namespace is used or executed here:
every ELF is a locally built stand-in, every identity value is computed from
those synthetic bytes, and the executor-facing v2 launch plan is validated as
a generated document. The real Linux INPUT builder is exercised against a
synthetic pinned interpreter, synthetic distributions and a synthetic git
checkout. The six official cases are NOT this node's completion condition.
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
from types import SimpleNamespace

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
# Stand-in ELF shapes of the real Linux INPUT runtime members: the payload
# interpreter, a packaged extension module, the dynamic loader, the shell and
# a leaf shared library. Never executed by anything.
PYTHON3_ELF = build_elf(needed=('libc.so.6', 'libz.so.1'),
                        interp='/lib64/ld-linux-x86-64.so.2')
EXTENSION_ELF = build_elf(needed=('libc.so.6',), interp=None)
LD_ELF = build_elf(needed=('libc.so.6',), interp=None)
SHELL_ELF = build_elf(needed=('libc.so.6',), interp='/lib64/ld-linux-x86-64.so.2')
LIBC_ELF = build_elf(needed=(), interp=None)


@pytest.fixture(autouse=True)
def synthetic_host_runtime(tmp_path, monkeypatch):
    """Synthetic measured host runtime: soname directories, ld.so and /bin/sh.

    The generator resolves and measures loader/library files on the Linux
    host; these synthetic plain stand-ins make that resolution testable here
    without any host library, real binary or execution.
    """
    root = tmp_path/'host-runtime'
    lib = root/'lib'/'x86_64-linux-gnu'
    lib.mkdir(parents=True)
    lib64 = root/'lib64'
    lib64.mkdir()
    for name in ('libc.so.6', 'libgcc_s.so.1', 'libz.so.1'):
        (lib/name).write_bytes(LIBC_ELF)
    (lib64/'ld-linux-x86-64.so.2').write_bytes(LD_ELF)
    shell = root/'bin-sh'
    shell.write_bytes(SHELL_ELF)
    monkeypatch.setattr(e, 'LINUX_RUNTIME_LIBRARY_DIRS', (str(lib), str(lib64)))
    monkeypatch.setattr(e, 'LINUX_SHELL_HOST_PATH', str(shell))
    return root


def assert_measured_interp_bind(by_guest, interp):
    """Assert an interpreter bind carries the platform-truth measurement.

    Soname resolution is owned by the synthetic fixture, but an absolute
    interpreter path that genuinely exists on the host (the real
    /lib64/ld-linux-x86-64.so.2 on Linux) is deliberately measured from that
    host file - that is the production behavior under test; only where the
    canonical path is absent does resolution fall through to the fixture
    stand-in. The bind must pin exactly the file resolution chose, with
    sha256 and size measured from those very bytes.
    """
    entry = by_guest[interp]
    source = Path(os.path.realpath(str(e._linux_runtime_source(interp))))
    data = source.read_bytes()
    assert entry['source'] == str(source)
    assert entry['sha256'] == sha256(data).hexdigest()
    assert entry['bytes'] == len(data)
    if not os.path.lexists(interp):
        assert data == LD_ELF  # the fixture stand-in was the resolution result
    return data


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
        (root/'python/lib/python3.12/lib-dynload').mkdir(parents=True)
        (root/'python/lib/python3.12/lib-dynload/'
               '_ext.cpython-312-x86_64-linux-gnu.so').write_bytes(EXTENSION_ELF)
        (root/'python/bin').mkdir(parents=True)
        (root/'python/bin/python3').write_bytes(PYTHON3_ELF)
    m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
    (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    return root, m


def refresh_manifest(root):
    (root/'environment-manifest.json').unlink()
    m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
    (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    return m


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


def build_elf_split_dynstr(needed=('libpthread.so.0', 'libdl.so.2', 'libutil.so.1',
                                   'libm.so.6', 'librt.so.1', 'libc.so.6'),
                           interp='/lib64/ld-linux-x86-64.so.2', strsz=None):
    """Real-linker layout: DT_STRSZ is recorded and .dynstr starts near the
    end of one LOAD segment and continues into the next contiguous one (the
    exact shape of the pinned CPython binary that broke single-segment
    reading). Never executed by anything."""
    base = 0x3ff000
    phoff, phnum = 64, 4
    interp_bytes = interp.encode('ascii') + b'\0'
    interp_off = phoff + 56*phnum
    dyn_off = interp_off + len(interp_bytes)
    strtab_off = 0xfe0                       # 32 bytes before the LOAD1 end
    strtab = b'\0' + b''.join(n.encode('ascii') + b'\0' for n in needed)
    total = strtab_off + len(strtab)
    image = bytearray(total)
    image[:16] = b'\x7fELF' + bytes([2, 1, 1, 0]) + b'\0'*8
    struct.pack_into('<HHIQQQIHHHHHH', image, 16, 2, 62, 1, 0x19b1200, phoff,
                     0, 0, 64, 56, phnum, 64, 0, 0)
    image[phoff:phoff+56*phnum] = b''.join((
        # LOAD1: file [0, 0x1000) at vaddr base; LOAD2 continues at 0x1000.
        struct.pack('<IIQQQQQQ', 1, 5, 0, base, 0, 0x1000, 0x1000, 0x1000),
        struct.pack('<IIQQQQQQ', 3, 4, interp_off, base + interp_off, 0,
                    len(interp_bytes), len(interp_bytes), 0x1),
        struct.pack('<IIQQQQQQ', 2, 6, dyn_off, base + dyn_off, 0, 16*(len(needed)+3),
                    16*(len(needed)+3), 0x8),
        struct.pack('<IIQQQQQQ', 1, 5, 0x1000, base + 0x1000, 0,
                    total - 0x1000, total - 0x1000, 0x1000)))
    image[interp_off:interp_off+len(interp_bytes)] = interp_bytes
    offsets = []
    position = 1
    for name in needed:
        offsets.append(position)
        position += len(name) + 1
    dynamic = b''.join(struct.pack('<QQ', 1, offset) for offset in offsets)
    dynamic += struct.pack('<QQ', 10, len(strtab) if strsz is None else strsz)
    dynamic += struct.pack('<QQ', 5, base + strtab_off)  # DT_STRTAB
    dynamic += struct.pack('<QQ', 0, 0)
    image[dyn_off:dyn_off+len(dynamic)] = dynamic
    image[strtab_off:strtab_off+len(strtab)] = strtab
    return bytes(image)


def test_linux_elf_dynstr_spanning_loads_is_parsed(tmp_path):
    # Regression for the real pinned CPython binary: its .dynstr crosses a
    # LOAD-segment boundary with DT_STRSZ recorded, which single-segment
    # strtab reading rejected as image_elf_invalid.
    elf = build_elf_split_dynstr()
    binary = tmp_path/'python3'
    binary.write_bytes(elf)
    facts = e._elf_facts(binary, len(elf), require_interp=False)
    assert facts['interp'] == '/lib64/ld-linux-x86-64.so.2'
    assert facts['needed'] == sorted(set(('libpthread.so.0', 'libdl.so.2',
                                          'libutil.so.1', 'libm.so.6',
                                          'librt.so.1', 'libc.so.6')))
    assert e._elf_facts(binary, len(elf)) == facts  # interp requirement met
    # A DT_STRSZ that outruns the LOAD map is still refused, bounded.
    (tmp_path/'broken').write_bytes(build_elf_split_dynstr(strsz=1 << 30))
    with pytest.raises(ValueError, match='image_elf_invalid'):
        e._elf_facts(tmp_path/'broken', (tmp_path/'broken').stat().st_size,
                     require_interp=False)


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
    exec_line = lines[exec_index]
    for fragment in ("import os; os.makedirs('/pal-output/launcher-tmp'); ",
                     "sys.path[:0]=['/pal-input/source','/pal-input/source/src',",
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


def test_linux_launcher_uses_shell_builtins_and_payload_python_only():
    # A1 choice: mkdir was removed (the payload Python creates output
    # directories), so no coreutils or other external command is invoked.
    text = e.official_launcher(valid_linux_manifest(), platform='linux').decode('ascii')
    for external in ('mkdir /pal-output', 'rm ', 'cp ', 'ln ', 'touch ', 'chmod ',
                     'ip link', '/usr/bin/', 'command ', 'env '):
        assert external not in text, external
    assert "os.makedirs('/pal-output/launcher-tmp')" in text
    assert 'qualify-version' not in text and 'official-six' not in text


def test_linux_a1_a2_a3_choices_are_recorded_in_source():
    source = (ROOT/'scripts/claude_probe_environment.py').read_text(encoding='utf-8')
    for marker in ('A1 record:', 'A2 record:', 'A3 record:'):
        assert marker in source, marker


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


# --- Namespace plan v2: synthetic namespace/networking/cleanup proofs -----

def test_linux_official_config_writes_reviewed_launch_plan(tmp_path):
    root, image, control = linux_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.json'
    result = e._official_config_generate(root, image, control, output, destination, 'linux')
    assert result['status'] == 'official_config_generated_not_launched'
    assert result['schema'] == 'research-linux-launch-v2'
    assert result['modes'] == ['qualify-version', 'official-six']
    assert result['runtime_binds'] >= 1
    assert result['namespaces'] == list(e.LINUX_NAMESPACES)
    assert result['runtime_needed'] == ['libc.so.6', 'libgcc_s.so.1']
    assert result['official_cli_executed'] is False and result['activation_authorized'] is False
    assert list(output.iterdir()) == []
    raw = destination.read_bytes()
    assert all(byte < 128 for byte in raw)
    plan = json.loads(raw)
    assert plan['schema'] == e.LINUX_PLAN_SCHEMA == 'research-linux-launch-v2'
    assert plan['generation'] == 'config_only_not_executed'
    assert plan['runner'] == {'bwrap_version': '0.11.1',
                              'execution': 'outer_runner_owned_separately',
                              'supervision': 'outside_workload_cgroup'}
    assert sorted(plan['namespaces']) == sorted(e.LINUX_NAMESPACES)
    assert plan['network'] == {'mode': 'loopback_only',
                               'external_egress': 'unavailable', 'address': '127.0.0.1',
                               'loopback': 'automatic_under_unshare_net_no_ip_command'}
    mounts = plan['mounts']
    assert [m['role'] for m in mounts] == ['INPUT', 'IMAGE', 'CONTROL', 'OUTPUT', 'SCRATCH', 'TMP']
    assert [m['readonly'] for m in mounts] == [True, True, True, False, False, False]
    assert [m['kind'] for m in mounts] == ['bind', 'bind', 'bind', 'tmpfs', 'tmpfs', 'tmpfs']
    by_role = {m['role']: m for m in mounts}
    assert by_role['INPUT'] == {'role': 'INPUT', 'host': str(root), 'guest': '/pal-input',
                                'readonly': True, 'kind': 'bind'}
    assert by_role['IMAGE']['host'] == str(image) and by_role['IMAGE']['guest'] == '/pal-claude-image'
    assert by_role['CONTROL']['host'] == str(control)
    assert by_role['OUTPUT'] == {'role': 'OUTPUT', 'host': str(output), 'guest': '/pal-output',
                                 'readonly': False, 'kind': 'tmpfs',
                                 'size_limit_bytes': e.LINUX_EXPORT_BYTES,
                                 'host_role': 'export_destination'}
    assert by_role['SCRATCH'] == {'role': 'SCRATCH', 'host': None, 'guest': '/pal-scratch',
                                  'readonly': False, 'kind': 'tmpfs',
                                  'size_limit_bytes': e.LINUX_SCRATCH_BYTES}
    assert by_role['TMP'] == {'role': 'TMP', 'host': None, 'guest': '/tmp',
                              'readonly': False, 'kind': 'tmpfs',
                              'size_limit_bytes': e.LINUX_TMP_BYTES}
    assert plan['export'] == {'destination': str(output),
                              'bounded_bytes': e.LINUX_EXPORT_BYTES,
                              'creation': 'exclusive_no_follow',
                              'mounted_writable_in_namespace': False}
    launcher_bytes = e.official_launcher(valid_linux_manifest(), platform='linux')
    assert plan['launcher'] == {'path': str(control)+'/official-probe.sh',
                                'sha256': sha256(launcher_bytes).hexdigest(),
                                'bytes': len(launcher_bytes)}
    binds = plan['runtime_binds']
    by_guest = {b['guest']: b for b in binds}
    assert [b['guest'] for b in binds] == sorted(by_guest)
    library = e.LINUX_RUNTIME_LIBRARY_DIRS[0]
    for guest in ('/bin/sh', '/pal-input/python/bin/python3',
                  '/lib64/ld-linux-x86-64.so.2', f'{library}/libc.so.6',
                  f'{library}/libgcc_s.so.1', f'{library}/libz.so.1'):
        assert guest in by_guest, guest
    assert by_guest['/bin/sh']['sha256'] == sha256(SHELL_ELF).hexdigest()
    assert_measured_interp_bind(by_guest, '/lib64/ld-linux-x86-64.so.2')
    assert by_guest['/pal-input/python/bin/python3']['sha256'] == sha256(PYTHON3_ELF).hexdigest()
    assert by_guest[f'{library}/libc.so.6']['bytes'] == len(LIBC_ELF)
    for entry in binds:
        assert entry['mode'] == 'ro'
        data = Path(entry['source']).read_bytes()
        assert entry['sha256'] == sha256(data).hexdigest() and entry['bytes'] == len(data)
    assert plan['runtime_layout'] == {'guest_paths': 'canonical',
                                      'ld_library_path': 'not_used',
                                      'library_search': list(e.LINUX_RUNTIME_LIBRARY_DIRS),
                                      'launcher_externals': 'shell_builtins_and_payload_python_only',
                                      'shell_guest': '/bin/sh',
                                      'shell_source': by_guest['/bin/sh']['source']}
    assert plan['environment'] == {'clearenv': True, 'setenv': {'PATH': '/usr/bin:/bin'}}
    assert plan['modes'] == [
        {'mode': 'qualify-version',
         'selection': 'outer_runner_final_command_replacement',
         'command': ['/pal-claude-image/claude', '--version'],
         'expected_banner': '2.1.278 (Claude Code)',
         'synthetic_request': False, 'depends_on': []},
        {'mode': 'official-six', 'selection': 'plan_argv_final_command',
         'command': ['/pal-control/official-probe.sh', '--isolated-host-attested'],
         'expected_banner': None, 'synthetic_request': True,
         'depends_on': ['qualify-version']}]
    argv = plan['argv']
    assert argv[0] == 'bwrap'
    for flag in ('--unshare-user', '--unshare-ipc', '--unshare-pid', '--unshare-net',
                 '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
                 '--dev', '/dev', '--proc', '/proc', '--cap-drop', 'ALL'):
        assert argv.count(flag) == 1, flag
    index = argv.index('--clearenv')
    assert argv[index+1:index+4] == ['--setenv', 'PATH', '/usr/bin:/bin']
    assert argv.count('--setenv') == 1
    assert any(argv[i:i+2] == ['--tmpfs', '/'] for i in range(len(argv)-1))
    for sequence in (('--size', str(e.LINUX_SCRATCH_BYTES), '--tmpfs', e.LINUX_GUESTS['scratch']),
                     ('--size', str(e.LINUX_TMP_BYTES), '--tmpfs', '/tmp'),
                     ('--size', str(e.LINUX_EXPORT_BYTES), '--tmpfs', '/pal-output')):
        assert any(tuple(argv[i:i+4]) == sequence for i in range(len(argv)-3)), sequence
    assert argv.count('--tmpfs') == 4 and argv.count('--size') == 3
    assert '--sizelimit' not in argv and '--bind' not in argv
    assert not any(item == 'ip' or item.startswith('ip ') for item in argv)
    pairs = {(argv[i+1], argv[i+2]) for i in range(len(argv)-2) if argv[i] == '--ro-bind'}
    assert pairs == ({(str(root), '/pal-input'), (str(image), '/pal-claude-image'),
                      (str(control), '/pal-control')}
                     | {(b['source'], b['guest']) for b in binds})
    assert argv.count('--ro-bind') == 3 + len(binds)
    assert argv[-2:] == ['/pal-control/official-probe.sh', '--isolated-host-attested']
    assert sorted(plan['excluded_host_surfaces']) == sorted(e.LINUX_EXCLUDED_SURFACES)
    assert plan['bounds'] == {'memory_mb': 4096, 'memory_swap_max': 0, 'pids_max': 64,
                              'deadline_seconds': 900,
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


def test_linux_v1_generation_only_plans_are_executor_rejected():
    assert e.LINUX_PLAN_SCHEMA == 'research-linux-launch-v2'
    assert e.LINUX_PLAN_SCHEMA_V1 == 'claude-probe-namespace-linux-v1'
    legacy = dict(schema=e.LINUX_PLAN_SCHEMA_V1, generation='config_only_not_executed',
                  argv=['bwrap'], namespaces=list(e.LINUX_NAMESPACES))
    assert e._linux_namespace_plan_problem(legacy) == 'namespace_plan_invalid'


def test_linux_plan_launcher_identity_pins_written_control_bytes(tmp_path):
    # The emitted launcher block is MEASURED from the exact launcher bytes on
    # disk in CONTROL, so a host-level swap between generation and execution
    # is detectable by the outer runner's admission.
    root, image, control = linux_setup(tmp_path)
    destination = tmp_path/'official-probe.json'
    e._official_config_generate(root, image, control, tmp_path/'out', destination, 'linux')
    plan = json.loads(destination.read_bytes())
    written = (control/'official-probe.sh').read_bytes()
    assert plan['launcher'] == {'path': str(control)+'/official-probe.sh',
                                'sha256': sha256(written).hexdigest(),
                                'bytes': len(written)}
    assert Path(plan['launcher']['path']).read_bytes() == written
    # a host-level edit after generation no longer matches the pinned block:
    # the admission comparison is on-disk digest vs plan launcher sha256
    (control/'official-probe.sh').write_bytes(written + b'# swapped\n')
    swapped = (control/'official-probe.sh').read_bytes()
    assert swapped != written
    assert sha256(swapped).hexdigest() != plan['launcher']['sha256']


def test_linux_output_is_export_destination_never_writable_mount(tmp_path):
    root, image, control = linux_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.json'
    e._official_config_generate(root, image, control, output, destination, 'linux')
    plan = json.loads(destination.read_bytes())
    by_role = {m['role']: m for m in plan['mounts']}
    assert by_role['OUTPUT']['kind'] == 'tmpfs'
    assert by_role['OUTPUT']['host_role'] == 'export_destination'
    assert by_role['OUTPUT']['size_limit_bytes'] == e.LINUX_EXPORT_BYTES == 67108864
    assert plan['export'] == {'destination': str(output),
                              'bounded_bytes': 67108864,
                              'creation': 'exclusive_no_follow',
                              'mounted_writable_in_namespace': False}
    argv = plan['argv']
    assert not any(flag in argv for flag in ('--bind', '--dev-bind', '--bind-try',
                                             '--ro-bind-try', '--dev-bind-try'))
    # the host export destination path appears in no bind operand at all
    operands = {argv[i+1] for i in range(len(argv)-1) if argv[i].endswith('bind')}
    assert str(output) not in operands


def test_linux_environment_is_explicitly_set_not_bare_cleared(tmp_path):
    root, image, control = linux_setup(tmp_path)
    destination = tmp_path/'official-probe.json'
    e._official_config_generate(root, image, control, tmp_path/'out', destination, 'linux')
    plan = json.loads(destination.read_bytes())
    argv = plan['argv']
    index = argv.index('--clearenv')
    assert argv[index+1:index+4] == ['--setenv', 'PATH', '/usr/bin:/bin']
    assert argv.count('--setenv') == len(plan['environment']['setenv']) == 1
    assert plan['environment'] == {'clearenv': True, 'setenv': {'PATH': '/usr/bin:/bin'}}


def test_linux_qualify_version_mode_pins_one_version_invocation(tmp_path):
    root, image, control = linux_setup(tmp_path)
    destination = tmp_path/'official-probe.json'
    e._official_config_generate(root, image, control, tmp_path/'out', destination, 'linux')
    plan = json.loads(destination.read_bytes())
    qualify, batch = plan['modes']
    assert qualify['mode'] == 'qualify-version'
    assert qualify['command'] == ['/pal-claude-image/claude', '--version']
    assert qualify['synthetic_request'] is False and qualify['depends_on'] == []
    assert qualify['expected_banner'] == '2.1.278 (Claude Code)'
    assert batch['mode'] == 'official-six'
    assert batch['command'] == plan['argv'][-2:]
    assert batch['expected_banner'] is None and batch['synthetic_request'] is True
    assert batch['depends_on'] == ['qualify-version']
    assert [mode['mode'] for mode in plan['modes']] == ['qualify-version', 'official-six']


def test_linux_runtime_closure_is_measured_recursive_and_deterministic(tmp_path):
    root, _ = linux_payload(tmp_path)
    image = write_linux_image(tmp_path)
    payload_value = e.verify(root)
    value, facts = e._load_official_image(image, 'linux')
    names = [entry['path'] for entry in payload_value['files']]
    binds = e._linux_runtime_closure(root, names, facts)
    assert binds == e._linux_runtime_closure(root, names, facts)
    by_guest = {b['guest']: b for b in binds}
    library = e.LINUX_RUNTIME_LIBRARY_DIRS[0]
    expected = {'/lib64/ld-linux-x86-64.so.2', '/bin/sh',
                '/pal-input/python/bin/python3', f'{library}/libc.so.6',
                f'{library}/libgcc_s.so.1', f'{library}/libz.so.1'}
    assert expected <= set(by_guest)
    for entry in binds:
        data = Path(entry['source']).read_bytes()
        assert entry['sha256'] == sha256(data).hexdigest()
        assert entry['bytes'] == len(data) and entry['mode'] == 'ro'
    assert by_guest['/bin/sh']['sha256'] == sha256(SHELL_ELF).hexdigest()
    assert_measured_interp_bind(by_guest, '/lib64/ld-linux-x86-64.so.2')
    assert by_guest['/pal-input/python/bin/python3']['sha256'] == sha256(PYTHON3_ELF).hexdigest()


def test_linux_runtime_closure_binds_ld_at_both_canonical_guests(tmp_path):
    # The real official ELF lists ld-linux-x86-64.so.2 among its DT_NEEDED
    # while its PT_INTERP names /lib64/ld-linux-x86-64.so.2, and usr-merged
    # hosts realpath both onto one file: one measured source may back both
    # canonical guest paths - but only ever with a single identity.
    elf = build_elf(needed=('ld-linux-x86-64.so.2', 'libc.so.6'))
    image = write_linux_image(tmp_path, data=elf)
    root, _ = linux_payload(tmp_path)
    payload_value = e.verify(root)
    value, facts = e._load_official_image(image, 'linux')
    names = [entry['path'] for entry in payload_value['files']]
    binds = e._linux_runtime_closure(root, names, facts)
    by_guest = {b['guest']: b for b in binds}
    soname = by_guest[f'{e.LINUX_RUNTIME_LIBRARY_DIRS[1]}/ld-linux-x86-64.so.2']
    # Platform truth: the canonical /lib64 interp path is measured from the
    # real host ld.so where it exists (Linux); the soname guest always
    # resolves through the fixture. Where the canonical path is absent, both
    # guests resolve onto ONE measured source - the duplicate-source shape.
    assert_measured_interp_bind(by_guest, '/lib64/ld-linux-x86-64.so.2')
    interp = by_guest['/lib64/ld-linux-x86-64.so.2']
    if os.path.lexists('/lib64/ld-linux-x86-64.so.2'):
        assert soname['source'] != interp['source']
    else:
        assert soname['source'] == interp['source']
        assert soname['sha256'] == interp['sha256']
        assert soname['bytes'] == interp['bytes']
    plan = e._linux_namespace_plan(root, payload_value, image, tmp_path/'control',
                                   tmp_path/'out', value, facts)
    assert e._linux_namespace_plan_problem(plan) is None
    # One source, two identities is refused - grafted here so the invariant
    # is exercised identically on every host, regardless of how the closure
    # resolved the canonical interp path.
    grafted = json.loads(json.dumps(plan))
    interp_bind = next(b for b in grafted['runtime_binds']
                       if b['guest'] == '/lib64/ld-linux-x86-64.so.2')
    extra = dict(interp_bind, guest='/synthetic/second-guest', sha256='f'*64)
    grafted['runtime_binds'].append(extra)
    grafted['argv'] = (grafted['argv'][:-2]
                       + ['--ro-bind', extra['source'], extra['guest']]
                       + grafted['argv'][-2:])
    assert e._linux_namespace_plan_problem(grafted) == 'namespace_plan_invalid'
    # The same graft with the SAME identity is the legitimate shape.
    grafted['runtime_binds'][-1]['sha256'] = interp_bind['sha256']
    assert e._linux_namespace_plan_problem(grafted) is None


def test_linux_runtime_closure_fails_closed_on_gaps(tmp_path, monkeypatch):
    root, _ = linux_payload(tmp_path)
    image = write_linux_image(tmp_path)
    payload_value = e.verify(root)
    value, facts = e._load_official_image(image, 'linux')
    names = [entry['path'] for entry in payload_value['files']]
    real_cap = e.LINUX_MAX_RUNTIME_BINDS
    monkeypatch.setattr(e, 'LINUX_MAX_RUNTIME_BINDS', 3)
    with pytest.raises(ValueError, match='runtime_closure_unbounded'):
        e._linux_runtime_closure(root, names, facts)
    monkeypatch.setattr(e, 'LINUX_MAX_RUNTIME_BINDS', real_cap)
    (root/'python/bin/python3').write_bytes(
        build_elf(needed=('libmissing.so.9',), interp='/lib64/ld-linux-x86-64.so.2'))
    with pytest.raises(ValueError, match='runtime_closure_incomplete'):
        e._linux_runtime_closure(root, names, facts)


def test_linux_config_requires_real_elf_payload_interpreter(tmp_path):
    root, _ = linux_payload(tmp_path)
    (root/'python/bin/python3').write_bytes(b'#!/bin/sh\nnot an ELF interpreter\n')
    refresh_manifest(root)
    image = write_linux_image(tmp_path)
    control = tmp_path/'control'
    e._official_control_generate(image, control, 'linux')
    with pytest.raises(ValueError, match='image_elf_invalid'):
        e._official_config_generate(root, image, control, tmp_path/'out',
                                    tmp_path/'plan.json', 'linux')
    assert not (tmp_path/'out').exists() and not (tmp_path/'plan.json').exists()


@pytest.mark.parametrize('mutation', [
    'schema', 'schema-v1', 'generation', 'runner-version', 'runner-supervision',
    'drop-namespace', 'extra-namespace', 'network-shared', 'network-egress',
    'network-ip-mode', 'writable-input', 'writable-image', 'guest-swap',
    'no-die-with-parent', 'no-new-session', 'no-clearenv', 'cap-drop-partial',
    'setenv-extra', 'setenv-missing', 'bind-image-writable', 'argv-prefix',
    'inner-no-attest', 'ip-wrapper', 'ip-element', 'child-env-home',
    'excluded-empty', 'bounds-memory', 'bounds-pids', 'bounds-deadline',
    'executed-true', 'authorized-true', 'closure-interp-relative',
    'closure-unsorted', 'closure-invented-member', 'mounts-count',
    'mounts-reorder', 'scratch-size', 'tmp-size', 'export-size', 'export-role',
    'export-destination-swap', 'output-kind-bind', 'launcher-drop',
    'launcher-sha', 'launcher-bytes', 'launcher-path', 'runtime-bind-drop',
    'runtime-bind-guest-duplicate', 'runtime-bind-source-forged',
    'runtime-bind-mode-rw', 'layout-ld-path', 'layout-externals',
    'modes-count', 'mode-banner', 'mode-selection', 'mode-command',
    'tmpfs-count', 'size-tmp-detach', 'size-tmp-inflate',
    'size-syntax-sizelimit', 'tmpfs-root-drop', 'no-proc',
    'unknown-flag-dev-bind', 'unknown-flag-bind-try'])
def test_linux_launch_plan_self_check_rejects_tampering(tmp_path, mutation):
    root, image, control = linux_setup(tmp_path)
    payload_value = e.verify(root)
    value, facts = e._load_official_image(image, 'linux')
    plan = e._linux_namespace_plan(root, payload_value, image, control,
                                   tmp_path/'out', value, facts)
    argv = plan['argv']; binds = plan['runtime_binds']; modes = plan['modes']
    if mutation == 'schema':
        plan['schema'] = 'other'
    elif mutation == 'schema-v1':
        plan['schema'] = e.LINUX_PLAN_SCHEMA_V1
    elif mutation == 'generation':
        plan['generation'] = 'executed'
    elif mutation == 'runner-version':
        plan['runner']['bwrap_version'] = '0.10.0'
    elif mutation == 'drop-namespace':
        plan['namespaces'].remove('pid')
    elif mutation == 'extra-namespace':
        plan['namespaces'].append('cgroup')
    elif mutation == 'network-shared':
        plan['network']['mode'] = 'shared'
    elif mutation == 'network-egress':
        plan['network']['external_egress'] = 'available'
    elif mutation == 'network-ip-mode':
        plan['network']['loopback'] = 'ip_link_command'
    elif mutation in ('writable-input', 'writable-image'):
        plan['mounts'][0 if mutation == 'writable-input' else 1]['readonly'] = False
    elif mutation == 'guest-swap':
        plan['mounts'][0]['guest'], plan['mounts'][3]['guest'] = \
            plan['mounts'][3]['guest'], plan['mounts'][0]['guest']
    elif mutation in ('no-die-with-parent', 'no-new-session', 'no-clearenv'):
        argv.remove('--'+mutation.removeprefix('no-'))
    elif mutation == 'cap-drop-partial':
        index = argv.index('--cap-drop')
        argv[index+1] = 'NET_RAW'
    elif mutation == 'setenv-extra':
        plan['environment']['setenv']['HOME'] = '/root'
    elif mutation == 'setenv-missing':
        plan['environment']['setenv'].pop('PATH')
    elif mutation == 'bind-image-writable':
        index = next(i for i in range(len(argv)-2)
                     if argv[i] == '--ro-bind' and argv[i+1] == str(image))
        argv[index] = '--bind'
    elif mutation == 'argv-prefix':
        argv[0] = 'docker'
    elif mutation == 'inner-no-attest':
        argv[-1] = '--attested'
    elif mutation == 'ip-wrapper':
        argv[-2:] = ['/bin/sh', '-c',
                     'ip link set lo up && exec /pal-control/official-probe.sh'
                     ' --isolated-host-attested']
    elif mutation == 'ip-element':
        argv.insert(1, 'ip')
    elif mutation == 'child-env-home':
        plan['environment']['setenv'] = {'PATH': '/usr/bin:/bin', 'HOME': '/root'}
    elif mutation == 'excluded-empty':
        plan['excluded_host_surfaces'] = []
    elif mutation == 'bounds-memory':
        plan['bounds']['memory_mb'] = 8192
    elif mutation == 'bounds-pids':
        plan['bounds']['pids_max'] = 128
    elif mutation == 'bounds-deadline':
        plan['bounds']['deadline_seconds'] = 300
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
    elif mutation == 'mounts-reorder':
        plan['mounts'][3], plan['mounts'][4] = plan['mounts'][4], plan['mounts'][3]
    elif mutation == 'scratch-size':
        plan['mounts'][4]['size_limit_bytes'] = 0
    elif mutation == 'tmp-size':
        plan['mounts'][5]['size_limit_bytes'] = 0
    elif mutation == 'export-size':
        plan['export']['bounded_bytes'] = 1
    elif mutation == 'export-role':
        plan['mounts'][3]['host_role'] = 'writable_mount'
    elif mutation == 'export-destination-swap':
        plan['export']['destination'] = '/elsewhere'
    elif mutation == 'output-kind-bind':
        plan['mounts'][3]['kind'] = 'bind'
    elif mutation == 'launcher-drop':
        plan.pop('launcher')
    elif mutation == 'launcher-sha':
        plan['launcher']['sha256'] = '0'*64
    elif mutation == 'launcher-bytes':
        plan['launcher']['bytes'] = plan['launcher']['bytes'] + 1
    elif mutation == 'launcher-path':
        plan['launcher']['path'] = '/elsewhere/official-probe.sh'
    elif mutation == 'runtime-bind-drop':
        binds.pop()
    elif mutation == 'runtime-bind-guest-duplicate':
        binds[1]['guest'] = binds[0]['guest']
    elif mutation == 'runtime-bind-source-forged':
        binds[0]['source'] = '/forged-source'
    elif mutation == 'runtime-bind-mode-rw':
        binds[0]['mode'] = 'rw'
    elif mutation == 'layout-ld-path':
        plan['runtime_layout']['ld_library_path'] = '/opt/libs'
    elif mutation == 'layout-externals':
        plan['runtime_layout']['launcher_externals'] = 'mkdir_and_coreutils'
    elif mutation == 'modes-count':
        modes.pop()
    elif mutation == 'mode-banner':
        modes[0]['expected_banner'] = '2.1.277 (Claude Code)'
    elif mutation == 'mode-selection':
        modes[0]['selection'] = 'launcher_argument'
    elif mutation == 'mode-command':
        modes[0]['command'] = ['/pal-claude-image/claude', '--version', '--extra']
    elif mutation == 'tmpfs-count':
        argv.remove('/tmp')
    elif mutation == 'size-tmp-detach':
        index = argv.index('/tmp')
        del argv[index-3:index-1]
    elif mutation == 'size-tmp-inflate':
        index = argv.index('/tmp')
        argv[index-2] = '999'
    elif mutation == 'size-syntax-sizelimit':
        index = argv.index('/tmp')
        argv[index-3] = '--sizelimit'
    elif mutation == 'tmpfs-root-drop':
        index = argv.index('/')
        del argv[index-1:index+1]
    elif mutation == 'no-proc':
        argv.remove('--proc')
    elif mutation == 'unknown-flag-dev-bind':
        index = argv.index('--ro-bind')
        argv[index:index] = ['--dev-bind', '/etc']
    elif mutation == 'unknown-flag-bind-try':
        argv.insert(len(argv)-2, '--bind-try')
    else:
        plan['runner']['supervision'] = 'inside_workload_cgroup'
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
    # Restore only the patched write (not the shared autouse runtime patches).
    monkeypatch.setattr(e, '_linux_exclusive_write', real)
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
    monkeypatch.setattr(e, '_exclusive_write', real_write)
    with pytest.raises(ValueError, match='output_dir_exists'):
        e._official_config_generate(root, image, control, output, plan, 'linux')


# --- Real Linux INPUT payload builder (synthetic stand-ins only) ------------

LINUX_DEP_VERSIONS = {name: f'1.{index}.0' for index, name in enumerate(e.DEPS_LINUX)}


def test_linux_dependency_tuple_is_the_linux_payload_closure():
    # Platform rationale: colorama reaches the payload only through pytest's
    # win32 marker, so a correctly synced Linux venv (and lock view) never
    # has it; tzdata must be carried because the namespace has NO system
    # timezone data. The Windows DEPS tuple stays frozen and separate.
    assert e.DEPS_LINUX == ('pytest', 'tzdata', 'iniconfig', 'packaging',
                            'pluggy', 'pygments')
    assert 'colorama' not in e.DEPS_LINUX
    assert 'tzdata' in e.DEPS_LINUX
    assert 'colorama' in e.DEPS and 'tzdata' in e.DEPS  # frozen Windows tuple
    assert set(e.DEPS_LINUX) < set(e.DEPS)


def test_linux_stdlib_headless_exclusion_surface_is_pinned():
    # Headless namespace, no display: the tkinter surface (the _tkinter
    # extension with its unresolvable Tcl9/Tk9 DT_NEEDED chain, the tkinter
    # package and its turtle.py front end) never enters the payload; pure
    # Python surfaces that merely import tkinter (idlelib, turtledemo) stay,
    # complete and inert, as does every other extension module whose
    # DT_NEEDED the pinned host directories do provide.
    excluded = ('tkinter/__init__.py', 'tkinter/test/support.py', 'turtle.py',
                'lib-dynload/_tkinter.cpython-312-x86_64-linux-gnu.so')
    kept = ('os.py', 'encodings/__init__.py', 'encodings/turtle.py',
            'lib-dynload/zlib.cpython-312-x86_64-linux-gnu.so',
            'idlelib/debugger.py', 'turtledemo/__main__.py')
    for name in excluded:
        assert e._linux_stdlib_excluded(name) is True, name
    for name in kept:
        assert e._linux_stdlib_excluded(name) is False, name
    assert e.LINUX_STDLIB_EXCLUDED_PACKAGES == ('tkinter',)
    assert e.LINUX_STDLIB_EXCLUDED_MODULES == ('turtle.py',)
    assert e.LINUX_STDLIB_EXCLUDED_EXTENSIONS == ('_tkinter',)


class SyntheticDistribution:
    """A fake installed distribution whose files live in a synthetic tree."""

    def __init__(self, root, name, version, extra_files=()):
        self.version = version
        self._home = root/name
        (self._home/name).mkdir(parents=True, exist_ok=True)
        (self._home/name/'__init__.py').write_bytes(f'# synthetic {name}\n'.encode())
        info = self._home/f'{name}-{version}.dist-info'
        info.mkdir(parents=True, exist_ok=True)
        (info/'METADATA').write_bytes(b'Metadata-Version: 2.1\n')
        self.files = [f'{name}/__init__.py',
                      f'{name}-{version}.dist-info/METADATA', *extra_files]
        for extra in extra_files:
            target = self._home/extra
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'payload file\n')

    def locate_file(self, entry):
        return self._home/str(entry)


def synthetic_build_env(parent, *, pth=False):
    """Synthetic pinned interpreter, distributions and committed git source."""
    home = parent/'build-env'
    installed = []
    for name in e.DEPS_LINUX:
        extra = (f'{name}/evil.pth',) if pth and name == 'pytest' else ()
        installed.append(SyntheticDistribution(
            home/'dists', name, LINUX_DEP_VERSIONS[name], extra))
    base = home/'cpython-3.12.14'
    stdlib = base/'lib'/'python3.12'
    stdlib.mkdir(parents=True)
    (base/'bin').mkdir(parents=True)
    (base/'bin'/'python3.12').write_bytes(
        b'PAL synthetic CPython 3.12.14 binary; never executed\n')
    (stdlib/'os.py').write_bytes(b'# stdlib stand-in\n')
    (stdlib/'encodings').mkdir(parents=True)
    (stdlib/'encodings'/'__init__.py').write_bytes(b'# encodings stand-in\n')
    dyn = stdlib/'lib-dynload'; dyn.mkdir()
    (dyn/'_ext.cpython-312-x86_64-linux-gnu.so').write_bytes(b'\x7fELF synthetic\n')
    # The real host defect: _tkinter links Tcl9/Tk9, which no pinned host
    # library directory provides (and a headless probe wants no GUI stack).
    (dyn/'_tkinter.cpython-312-x86_64-linux-gnu.so').write_bytes(
        build_elf(needed=('libtcl9.0.so', 'libtk9.0.so'), interp=None))
    (stdlib/'tkinter').mkdir()
    (stdlib/'tkinter'/'__init__.py').write_bytes(b'# tkinter stand-in\n')
    (stdlib/'turtle.py').write_bytes(b'# turtle stand-in\n')
    cache = stdlib/'__pycache__'; cache.mkdir()
    (cache/'os.cpython-312.pyc').write_bytes(b'host cache never enters')
    site = stdlib/'site-packages'; site.mkdir()
    (site/'host-junk.py').write_bytes(b'host site-packages never enters\n')
    repository = parent/'git-source'; repository.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repository), *args],
                                       stderr=subprocess.PIPE)
    git('init')
    for name in ('src/sample.py', *e.SOURCE_EXTRA):
        target = repository/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'# committed linux payload source\n')
    (repository/'uv.lock').write_text(
        ''.join(f'[[package]]\nname = "{name}"\n'
                f'version = "{LINUX_DEP_VERSIONS[name]}"\n\n' for name in e.DEPS_LINUX),
        encoding='utf-8')
    git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@invalid',
        'commit', '-m', 'synthetic linux payload source')
    def distributions():
        yield from zip(e.DEPS_LINUX, installed)
    return base, stdlib, distributions, repository


def linux_build_setup(parent, monkeypatch, *, pth=False):
    monkeypatch.setattr(e, '_LINUX_BUILD_READY', True)
    base, stdlib, distributions, repository = synthetic_build_env(parent, pth=pth)
    monkeypatch.setattr(e, '_linux_dependency_distributions', distributions)
    monkeypatch.setattr(e, '_linux_interpreter_layout',
                        lambda: (base/'bin'/'python3.12', stdlib))
    return base, stdlib, repository


def test_linux_build_assembles_fresh_symlink_free_input(tmp_path, monkeypatch):
    base, stdlib, repository = linux_build_setup(tmp_path, monkeypatch)
    calls = []
    real_chmod = os.chmod
    def recording(path, mode):
        calls.append((Path(path).name, mode))
        return real_chmod(path, mode)
    monkeypatch.setattr(e, '_LINUX_MODE_MEANINGFUL', True)
    monkeypatch.setattr(e.os, 'chmod', recording)
    destination = tmp_path/'linux-input'
    result = e.build_linux(repository, destination)
    assert result['status'] == 'linux_input_built_not_executed'
    assert result['python'] == sys.version.split()[0]
    assert result['dependencies'] == LINUX_DEP_VERSIONS
    assert result['official_cli_included'] is False
    assert result['official_cli_executed'] is False
    assert result['activation_authorized'] is False
    assert calls == [('python3', 0o755)]
    assert (destination/'python/bin/python3').read_bytes() == \
        (base/'bin'/'python3.12').read_bytes()
    names = {p.relative_to(destination).as_posix()
             for p in destination.rglob('*') if p.is_file()}
    for included in ('python/lib/python3.12/os.py',
                     'python/lib/python3.12/encodings/__init__.py',
                     'python/lib/python3.12/lib-dynload/_ext.cpython-312-x86_64-linux-gnu.so',
                     'environment-manifest.json', 'source/src/sample.py',
                     'source/pyproject.toml', 'source/uv.lock',
                     'source/tests/__init__.py',
                     'source/tests/claude_cli_probe.py',
                     'source/tests/test_research_claude_profile_native.py'):
        assert included in names, included
    for name in e.DEPS_LINUX:
        version = LINUX_DEP_VERSIONS[name]
        assert f'python/lib/python3.12/site-packages/{name}/__init__.py' in names
        assert (f'python/lib/python3.12/site-packages/'
                f'{name}-{version}.dist-info/METADATA') in names
    # colorama is a win32-marker dependency and never enters the Linux payload
    assert 'python/lib/python3.12/site-packages/colorama/__init__.py' not in names
    assert 'python/lib/python3.12/site-packages/tzdata/__init__.py' in names
    # Host caches, bytecode files and the interpreter's own site-packages
    # never enter the payload.
    assert not any('__pycache__' in name or name.endswith('.pyc') for name in names)
    assert 'python/lib/python3.12/site-packages/host-junk.py' not in names
    # The headless tkinter surface is excluded while the rest stays complete.
    for excluded in ('python/lib/python3.12/tkinter/__init__.py',
                     'python/lib/python3.12/turtle.py',
                     'python/lib/python3.12/lib-dynload/'
                     '_tkinter.cpython-312-x86_64-linux-gnu.so'):
        assert excluded not in names, excluded
    value = e.verify(destination)
    assert value['source_commit'] == result['source_commit']
    assert re.fullmatch('[0-9a-f]{40}', result['source_commit'])
    assert len(value['files']) == result['files']
    e._official_payload_ready(value, platform='linux')


@pytest.mark.parametrize('fault,expected', [
    ('host', 'linux_build_host_unsupported'),
    ('dirty', 'dirty_source'),
    ('unlocked', 'unlocked_dependency'),
    ('missing-dep', 'dependency_missing'),
    ('destination-exists', 'destination_exists'),
    ('runtime-inside-source', 'runtime_home_invalid'),
    ('pth', 'unexpected_dependency_path'),
])
def test_linux_build_refusals(tmp_path, monkeypatch, fault, expected):
    base, stdlib, repository = linux_build_setup(
        tmp_path, monkeypatch, pth=fault == 'pth')
    destination = tmp_path/'linux-input'
    if fault == 'host':
        monkeypatch.setattr(e, '_LINUX_BUILD_READY', False)
    elif fault == 'dirty':
        (repository/'uncommitted.txt').write_bytes(b'local edit')
    elif fault == 'unlocked':
        # installed versions that match no locked version (the lock itself
        # must stay committed and the checkout clean)
        def wrong_versions():
            for name in e.DEPS_LINUX:
                stub = SimpleNamespace(version='0.0.0', files=(),
                                       locate_file=lambda entry: tmp_path/'nowhere')
                yield name, stub
        monkeypatch.setattr(e, '_linux_dependency_distributions', wrong_versions)
    elif fault == 'missing-dep':
        def missing():
            e.fail('dependency_missing')
            yield
        monkeypatch.setattr(e, '_linux_dependency_distributions', missing)
    elif fault == 'destination-exists':
        destination.mkdir(); (destination/'kept').write_bytes(b'marker')
    elif fault == 'runtime-inside-source':
        monkeypatch.setattr(e, '_linux_interpreter_layout', lambda: (
            repository/'nested-runtime/bin/python3.12',
            repository/'nested-runtime/lib/python3.12'))
    with pytest.raises(ValueError, match=expected):
        e.build_linux(repository, destination)
    if fault == 'destination-exists':
        assert (destination/'kept').read_bytes() == b'marker'
    elif fault == 'pth':
        # the failed attempt is preserved, never deleted or reused
        assert destination.is_dir()
    else:
        assert not destination.exists()


def test_linux_build_refuses_host_symlinks(tmp_path, monkeypatch):
    base, stdlib, repository = linux_build_setup(tmp_path, monkeypatch)
    try:
        (stdlib/'os.py').unlink()
        os.symlink(base/'bin'/'python3.12', stdlib/'os.py')
    except OSError:
        pytest.skip('symlink permission unavailable on this host')
    with pytest.raises(ValueError):
        e.build_linux(repository, tmp_path/'linux-input')
    # the failed attempt is preserved, never deleted or reused
    assert (tmp_path/'linux-input'/'python/bin/python3').is_file()


def test_linux_build_cli_surface(monkeypatch, capsys, tmp_path):
    base, stdlib, distributions, repository = synthetic_build_env(tmp_path)
    monkeypatch.setattr(e, '_LINUX_BUILD_READY', False)
    monkeypatch.setattr(sys, 'argv', ['probe', 'build-linux', '--source', str(repository),
                                      '--destination', str(tmp_path/'input')])
    assert e.main() == 1
    assert json.loads(capsys.readouterr().out)['reason'] == 'linux_build_host_unsupported'
    assert not (tmp_path/'input').exists()
    monkeypatch.setattr(e, '_LINUX_BUILD_READY', True)
    monkeypatch.setattr(e, '_linux_dependency_distributions', distributions)
    monkeypatch.setattr(e, '_linux_interpreter_layout',
                        lambda: (base/'bin'/'python3.12', stdlib))
    monkeypatch.setattr(sys, 'argv', ['probe', 'build-linux', '--source', str(repository),
                                      '--destination', str(tmp_path/'input')])
    assert e.main() == 0
    status = json.loads(capsys.readouterr().out)
    assert status['status'] == 'linux_input_built_not_executed'
    assert status['activation_authorized'] is False
    assert (tmp_path/'input'/'environment-manifest.json').is_file()


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
