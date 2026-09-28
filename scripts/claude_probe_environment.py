"""Offline TEST packaging/preparation plus official-run CONFIG GENERATION.

Preparation modes (build/stage/verify/selftest) keep their reviewed behavior
and never launch a vendor CLI. The official-control/official-config generators
likewise execute no program: they only validate reviewed inputs and write the
control launcher plus the platform's configuration file. For Windows (frozen
historical behavior) the configuration is a four-mapping .wsb that, once
OPENED, runs the official launcher inside Windows Sandbox. For Linux a
build-linux preparation subcommand assembles the real INPUT payload (base
CPython 3.12.14 binary, complete standard library with extension modules,
lock-matched test dependencies, committed source/tests), and the
configuration is a rootless bwrap launch plan plus launcher companion
covering user/mount/PID/net/IPC/UTS namespaces, a fresh tmpfs guest root
with the measured recursive loader/library closure bound read-only at
canonical paths, loopback-only networking (automatic under --unshare-net,
no ip command), explicit clean environment, read-only INPUT/IMAGE/CONTROL,
sized tmpfs scratch, /tmp and /pal-output. The --output-dir argument is the
HOST EXPORT DESTINATION: bounded 64 MiB, never mounted writable into the
namespace; output crosses only through the /pal-output tmpfs. The plan pins
two fixed launcher modes (qualify-version, official-six) as data for the
separately owned outer runner. This node GENERATES configurations only;
executing an official binary is a separately qualified step that nothing
here performs.

The Linux artifact identity is OWNER-MEASURED: the pinned official Linux x86_64
Claude artifact's SHA256 and byte size are unmeasured upstream and enter only
through the reviewed image manifest. No digest, size or library closure value
is defaulted, embedded or invented by this generator; ELF structure, x86-64
architecture and the runtime library closure are derived from the image bytes.
Windows generation (claude.exe, .cmd, .wsb, Windows path validation) is frozen
history; pass --platform linux explicitly to select the Linux flavor.
Build only on a disposable Windows CI host. Stage/verify use stdlib and never
modify global tools, OS features, firewall or project business installations.
Generated Sandboxes have no network/clipboard and map only the reviewed
input/image/control/output folders. A smoke check or generated configuration
is not official-image acceptance or an isolation proof.
"""
from __future__ import annotations

import argparse
import ctypes
from hashlib import sha256
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET
import zipfile

MAX_FILES, MAX_BYTES, MAX_FILE = 25000, 1500000000, 150000000
# DEPS is the frozen Windows build tuple (colorama is pytest's win32-marker
# dependency there). The Linux payload tuple drops colorama - a correctly
# synced Linux venv never has it - and keeps tzdata, because the namespace
# has NO system timezone data and the payload must carry its own.
DEPS = ('pytest', 'tzdata', 'colorama', 'iniconfig', 'packaging', 'pluggy', 'pygments')
DEPS_LINUX = ('pytest', 'tzdata', 'iniconfig', 'packaging', 'pluggy', 'pygments')
SOURCE_EXTRA = ('tests/__init__.py', 'tests/claude_cli_probe.py',
                'tests/test_research_claude_profile_native.py', 'pyproject.toml', 'uv.lock')
SMOKE_CMD = (b'@echo off\r\nC:\\pal-input\\python\\python.exe -I -S -B '
             b'C:\\pal-input\\probe-environment.py selftest --root C:\\pal-input '
             b'--receipt C:\\pal-output\\environment.json\r\n')

OFFICIAL_IMAGE_MEMBER = 'claude.exe'
OFFICIAL_MANIFEST_NAME = 'image-manifest.json'
OFFICIAL_MANIFEST_MAX_BYTES = 4096
OFFICIAL_IMAGE_MAX_BYTES = 536870912
OFFICIAL_IMAGE_VERSION = '2.1.278'
OFFICIAL_IMAGE_KEYS = {'schema', 'path', 'sha256', 'bytes', 'version'}
OFFICIAL_IMAGE_INVENTORY = [OFFICIAL_IMAGE_MEMBER, OFFICIAL_MANIFEST_NAME]
OFFICIAL_LAUNCHER_NAME = 'official-probe.cmd'
OFFICIAL_CONTROL_INVENTORY = [OFFICIAL_LAUNCHER_NAME]
OFFICIAL_IMAGE_CHUNK = 1048576
OFFICIAL_DEVICE_STEMS = {'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
OFFICIAL_LAUNCHER_TEMPLATE = (
    b'@echo off\r\n'
    b'setlocal EnableExtensions DisableDelayedExpansion\r\n'
    b'if not "%~1"=="--isolated-host-attested" exit /b 2\r\n'
    b'if not "%~2"=="" exit /b 2\r\n'
    b'if not "%*"=="--isolated-host-attested" exit /b 2\r\n'
    b'\r\n'
    b'cd /d "C:\\pal-output"\r\n'
    b'if errorlevel 1 exit /b 2\r\n'
    b'if exist "C:\\pal-output\\launcher-tmp" exit /b 2\r\n'
    b'if exist "C:\\pal-output\\pytest-tmp" exit /b 2\r\n'
    b'if exist "C:\\pal-output\\pytest.log" exit /b 2\r\n'
    b'if exist "C:\\pal-output\\junit.xml" exit /b 2\r\n'
    b'if exist "C:\\pal-output\\exit-code.txt" exit /b 2\r\n'
    b'mkdir "C:\\pal-output\\launcher-tmp"\r\n'
    b'if errorlevel 1 exit /b 2\r\n'
    b'\r\n'
    b'set "POLYMARKET_ALPHA_LAB_CLAUDE_PROBE=1"\r\n'
    b'set "POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE=C:\\pal-claude-image\\claude.exe"\r\n'
    b'set "POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256={image_sha256}"\r\n'
    b'set "POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES={image_bytes}"\r\n'
    b'set "POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1"\r\n'
    b'set "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1"\r\n'
    b'set "PYTEST_ADDOPTS="\r\n'
    b'set "PYTEST_PLUGINS="\r\n'
    b'set "TMP=C:\\pal-output\\launcher-tmp"\r\n'
    b'set "TEMP=C:\\pal-output\\launcher-tmp"\r\n'
    b'\r\n'
    b'"C:\\pal-input\\python\\python.exe" -I -S -B -c "import sys; sys.path[:0]='
    b"[r'C:\\pal-input\\source',r'C:\\pal-input\\source\\src',"
    b"r'C:\\pal-input\\python\\Lib\\site-packages']; import pytest; "
    b"code=int(pytest.main(['-q','-s','--tb=short','-o','junit_family=legacy',"
    b"'-p','no:cacheprovider',r'--basetemp=C:\\pal-output\\pytest-tmp',"
    b"r'--junitxml=C:\\pal-output\\junit.xml',"
    b"r'C:\\pal-input\\source\\tests\\test_research_claude_profile_native.py'])); "
    b"receipt=open(r'C:\\pal-output\\exit-code.txt','x',encoding='ascii'); "
    b"receipt.write(str(code)+'\\n'); receipt.close(); raise SystemExit(code)\" "
    b'>"C:\\pal-output\\pytest.log" 2>&1\r\n'
    b'exit /b %ERRORLEVEL%\r\n'
)

# --- Linux official-probe preparation (config generation only) -------------
# The pinned official Linux x86_64 artifact identity (SHA256, byte size) is
# unmeasured upstream. It is a required owner-supplied parameter via the image
# manifest; this module defines NO digest/size defaults and invents no values.
LINUX_IMAGE_MEMBER = 'claude'
LINUX_IMAGE_SCHEMA = 'claude-probe-image-linux-v1'
LINUX_IMAGE_PLATFORM = 'linux-x86_64'
LINUX_IMAGE_KEYS = OFFICIAL_IMAGE_KEYS | {'platform'}
LINUX_LAUNCHER_NAME = 'official-probe.sh'
LINUX_CONTROL_INVENTORY = [LINUX_LAUNCHER_NAME]
# v1 was a generation-only document and is now executor-rejected; v2 is the
# executor-facing launch configuration consumed by the separately owned outer
# runner (the plan stays configuration; execution lives in that outer runner).
LINUX_PLAN_SCHEMA_V1 = 'claude-probe-namespace-linux-v1'
LINUX_PLAN_SCHEMA = 'research-linux-launch-v2'
LINUX_BWRAP_VERSION = '0.11.1'
LINUX_NAMESPACES = ('user', 'mount', 'pid', 'network', 'ipc', 'uts')
LINUX_GUESTS = {'input': '/pal-input', 'image': '/pal-claude-image',
                'control': '/pal-control', 'output': '/pal-output',
                'scratch': '/pal-scratch', 'tmp': '/tmp'}
LINUX_EXCLUDED_SURFACES = ('agent_sockets', 'authentication_state',
                           'database_directories', 'dot_local', 'dot_ssh',
                           'host_root', 'unrelated_configuration', 'user_home')
LINUX_CHILD_ENVIRONMENT = {'PATH': '/usr/bin:/bin'}
LINUX_SCRATCH_BYTES = 1073741824
LINUX_TMP_BYTES = 536870912
LINUX_EXPORT_BYTES = 67108864
LINUX_MEMORY_MB = 4096
LINUX_PIDS_MAX = 64
LINUX_DEADLINE_SECONDS = 900
LINUX_LOOPBACK_MODE = 'automatic_under_unshare_net_no_ip_command'
# A2 record: canonical ld.so search order. A soname resolves to the FIRST
# directory of this order providing it, and the resolved file is bound
# read-only at exactly that canonical guest path; LD_LIBRARY_PATH is NOT used.
LINUX_RUNTIME_LIBRARY_DIRS = ('/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu',
                              '/lib64', '/usr/lib64', '/usr/lib', '/lib')
LINUX_GUEST_SHELL = '/bin/sh'
LINUX_SHELL_HOST_PATH = '/bin/sh'
LINUX_MAX_RUNTIME_BINDS = 512
ELF_MAGIC = b'\x7fELF'
ELF_MAX_PHDRS = 1024
ELF_MAX_INTERP_BYTES = 4096
ELF_MAX_DYNAMIC_BYTES = 131072
ELF_MAX_STRTAB_BYTES = 1048576
ELF_MAX_NEEDED = 1024
ELF_MAX_SONAME = 4096
# The executable bit only exists on POSIX hosts; elsewhere mode checks no-op.
_LINUX_MODE_MEANINGFUL = os.name == 'posix'
# A1 record: the v2 launcher is constrained to /bin/sh BUILTINS plus the
# payload Python interpreter, and invokes NO external command - mkdir was
# removed and the payload Python creates the output directory before pytest
# runs. The measured runtime closure therefore only needs /bin/sh itself,
# python/bin/python3 and every packaged *.so (their loader dependencies), and
# the official image ELF closure; no coreutils binary is invoked by the
# launcher inside the namespace. Recorded here for the handoff.
LINUX_LAUNCHER_TEMPLATE = (
    b'#!/bin/sh\n'
    b'set -eu\n'
    b'if [ "${1-}" != "--isolated-host-attested" ]; then exit 2; fi\n'
    b'if [ "$#" -ne 1 ]; then exit 2; fi\n'
    b'cd /pal-output || exit 2\n'
    b'if [ ! -d /pal-output ]; then exit 2; fi\n'
    b'for name in launcher-tmp pytest-tmp pytest.log junit.xml exit-code.txt; do\n'
    b'  if [ -e "/pal-output/$name" ]; then exit 2; fi\n'
    b'done\n'
    b'export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE=1\n'
    b'export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE=/pal-claude-image/claude\n'
    b'export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256={image_sha256}\n'
    b'export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES={image_bytes}\n'
    b'export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1\n'
    b'export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1\n'
    b'unset PYTEST_ADDOPTS PYTEST_PLUGINS\n'
    b'export TMPDIR=/pal-output/launcher-tmp\n'
    b'exec /pal-input/python/bin/python3 -I -S -B -c "import os; '
    b"os.makedirs('/pal-output/launcher-tmp'); import sys; "
    b"sys.path[:0]=['/pal-input/source','/pal-input/source/src',"
    b"'/pal-input/python/lib/python3.12/site-packages']; import pytest; "
    b"code=int(pytest.main(['-q','-s','--tb=short','-o','junit_family=legacy',"
    b"'-p','no:cacheprovider','--basetemp=/pal-output/pytest-tmp',"
    b"'--junitxml=/pal-output/junit.xml',"
    b"'/pal-input/source/tests/test_research_claude_profile_native.py'])); "
    b"receipt=open('/pal-output/exit-code.txt','x',encoding='ascii'); "
    b"receipt.write(str(code)+'\\n'); receipt.close(); raise SystemExit(code)\" "
    b'> /pal-output/pytest.log 2>&1\n'
)


def fail(code):
    raise ValueError(code)


def clean_name(value):
    if (type(value) is not str or not value or len(value) > 240 or '\\' in value
            or any(ord(c) < 32 or ord(c) > 126 for c in value)):
        fail('invalid_bundle_path')
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or str(path) != value:
        fail('invalid_bundle_path')
    for part in path.parts:
        if (part in ('.', '..') or part.endswith((' ', '.')) or re.search(r'[:*?"<>|]', part)
                or part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                    *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}):
            fail('invalid_bundle_path')
    return path


def plain(path, *, directory=False):
    info = path.lstat()
    if (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            or not directory and info.st_nlink != 1):
        fail('nonplain_path')
    return info


def file_bytes(path):
    before = plain(path)
    if before.st_size > MAX_FILE:
        fail('file_too_large')
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if (len(data) != before.st_size or identity(before) != identity(after)
            or identity(before) != identity(plain(path))):
        fail('file_changed')
    return data


def walk(root):
    plain(root, directory=True)
    files, folded, total = {}, set(), 0
    def on_error(error):
        raise error
    for current, dirs, names in os.walk(root, followlinks=False, onerror=on_error):
        for name in dirs:
            plain(Path(current) / name, directory=True)
        for name in names:
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            clean_name(rel)
            size = plain(path).st_size
            total += size
            if len(files) >= MAX_FILES or size > MAX_FILE or total > MAX_BYTES:
                fail('bundle_too_large')
            if rel.casefold() in folded:
                fail('case_collision')
            files[rel] = path
            folded.add(rel.casefold())
    return files


def strict_json(data):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                fail('duplicate_manifest_key')
            value[key] = item
        return value
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: fail('invalid_number'))


def manifest(root, source_commit, source_tree, versions):
    entries = []
    for name, path in sorted(walk(root).items()):
        data = file_bytes(path)
        entries.append(dict(path=name, bytes=len(data), sha256=sha256(data).hexdigest()))
    return dict(schema='claude-probe-environment-v1', source_commit=source_commit,
                source_tree=source_tree, dependencies=versions, python=sys.version.split()[0],
                official_cli_included=False, activation_authorized=False, files=entries)


def verify(root):
    paths = walk(root)
    if 'environment-manifest.json' not in paths:
        fail('manifest_missing')
    value = strict_json(file_bytes(paths.pop('environment-manifest.json')))
    expected = {'schema', 'source_commit', 'source_tree', 'dependencies', 'python',
                'official_cli_included', 'activation_authorized', 'files'}
    if (type(value) is not dict or set(value) != expected
            or value['schema'] != 'claude-probe-environment-v1'
            or value['official_cli_included'] is not False or value['activation_authorized'] is not False
            or any(type(value[k]) is not str or not re.fullmatch('[0-9a-f]{40}', value[k])
                   for k in ('source_commit', 'source_tree'))
            or type(value['files']) is not list or not 1 <= len(value['files']) <= MAX_FILES):
        fail('manifest_invalid')
    seen = set()
    for entry in value['files']:
        if type(entry) is not dict or set(entry) != {'path', 'bytes', 'sha256'}:
            fail('manifest_invalid')
        name = entry['path']; clean_name(name)
        if (name in seen or name not in paths or type(entry['bytes']) is not int
                or not 0 <= entry['bytes'] <= MAX_FILE or type(entry['sha256']) is not str
                or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])):
            fail('manifest_invalid')
        data = file_bytes(paths[name])
        if len(data) != entry['bytes'] or sha256(data).hexdigest() != entry['sha256']:
            fail('content_mismatch')
        seen.add(name)
    if seen != set(paths):
        fail('unexpected_files')
    return value


def sandbox_xml(input_dir, output_dir):
    root = ET.Element('Configuration')
    for key, value in (('Networking', 'Disable'), ('ClipboardRedirection', 'Disable'),
            ('vGPU', 'Disable'), ('AudioInput', 'Disable'), ('VideoInput', 'Disable'),
            ('PrinterRedirection', 'Disable'), ('ProtectedClient', 'Enable'), ('MemoryInMB', '4096')):
        ET.SubElement(root, key).text = value
    mapped = ET.SubElement(root, 'MappedFolders')
    for host, guest, readonly in ((input_dir, r'C:\pal-input', 'true'),
                                 (output_dir, r'C:\pal-output', 'false')):
        # Sandbox expands percent variables; XML escaping does not disable that.
        if '%' in str(host) or any(ord(c) < 32 for c in str(host)):
            fail('mapping_path_invalid')
        folder = ET.SubElement(mapped, 'MappedFolder')
        for key, value in (('HostFolder', str(host)), ('SandboxFolder', guest), ('ReadOnly', readonly)):
            ET.SubElement(folder, key).text = value
    command = ET.SubElement(root, 'LogonCommand')
    ET.SubElement(command, 'Command').text = r'C:\Windows\System32\cmd.exe /d /c C:\pal-input\smoke.cmd'
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def stage(archive, digest, destination):
    """Verify then create a NEW preparation directory. Never launch anything."""
    if type(digest) is not str or not re.fullmatch('[0-9a-f]{64}', digest):
        fail('archive_digest_invalid')
    archive = archive.absolute(); destination = destination.absolute()
    # Reject link/reparse ancestors; do not create user-selected parents.
    for parent in (destination.parent, *destination.parent.parents):
        plain(parent, directory=True)
    if os.path.lexists(destination):
        fail('destination_exists')
    if '%' in str(destination) or any(ord(c) < 32 for c in str(destination)):
        fail('mapping_path_invalid')
    before = plain(archive)
    if before.st_size > 700000000:
        fail('archive_too_large')
    with archive.open('rb') as stream:
        actual = sha256()
        while block := stream.read(1048576): actual.update(block)
        if actual.hexdigest() != digest:
            fail('archive_hash_mismatch')
        stream.seek(0)
        with zipfile.ZipFile(stream) as z:
            infos = z.infolist(); seen, total = set(), 0
            for info in infos:
                name = info.filename; clean_name(name)
                mode = info.external_attr >> 16
                if (name.casefold() in seen or info.is_dir() or stat.S_ISLNK(mode)
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                        or info.flag_bits & 1 or not 0 <= info.file_size <= MAX_FILE):
                    fail('archive_entry_invalid')
                seen.add(name.casefold()); total += info.file_size
            if not infos or len(infos) > MAX_FILES or total > MAX_BYTES:
                fail('archive_bounds')
            destination.mkdir()
            payload = destination / 'input'; payload.mkdir()
            for info in infos:
                target = payload.joinpath(*clean_name(info.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                for parent in (target.parent, *target.parent.parents):
                    if parent == destination.parent:
                        break
                    plain(parent, directory=True)
                with z.open(info) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst, 65536)
    # Failed extraction/verification is preserved; never delete or reuse it.
    result = verify(payload)
    output = destination / 'output'; output.mkdir()
    (destination / 'preparation-smoke.wsb').write_bytes(sandbox_xml(payload, output))
    return dict(status='staged_not_launched', source_commit=result['source_commit'],
                official_cli_included=False, activation_authorized=False)


def selftest(root, receipt):
    """Only local Python/import/loopback checks; no CLI, auth, DB or pytest run."""
    sys.dont_write_bytecode = True
    if os.path.lexists(receipt): fail('receipt_exists')
    value = verify(root)
    if os.name != 'nt' or sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8:
        fail('runtime_platform_mismatch')
    if not Path(sys.executable).resolve().is_relative_to((root/'python').resolve()):
        fail('runtime_origin_mismatch')
    sys.path[:0] = [str(root/'source'), str(root/'source/src'), str(root/'python/Lib/site-packages')]
    import pytest
    import polymarket_alpha_lab
    from tests import claude_cli_probe
    for module in (pytest, polymarket_alpha_lab, claude_cli_probe):
        if not Path(module.__file__).resolve().is_relative_to(root.resolve()):
            fail('import_origin_mismatch')
    if claude_cli_probe.configured_image({}) is not None:
        fail('unexpected_default_cli')
    for name, version in value['dependencies'].items():
        if metadata.version(name) != version:
            fail('dependency_mismatch')
    # Both sides are numeric loopback. No DNS/external connect or scanner.
    with socket.socket() as server:
        server.settimeout(3); server.bind(('127.0.0.1', 0)); server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=3) as client:
            peer, _ = server.accept()
            with peer:
                peer.settimeout(3); client.sendall(b'PAL'); data = peer.recv(3)
                if data != b'PAL': fail('loopback_mismatch')
    verify(root)  # Read-only payload stays unchanged; no compile/pip writes.
    result = dict(status='preparation_smoke_passed', source_commit=value['source_commit'],
        python=sys.version.split()[0], dependencies=value['dependencies'],
        official_cli_included=False, official_cli_executed=False, official_cases_run=0,
        loopback_checked=True, sandbox_isolation_verified=False, activation_authorized=False)
    with receipt.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2); out.write('\n')
    return result


def committed_source_files(git):
    """Read committed bytes, not checkout EOL transformations; verify each blob.

    One archive avoids thousands of git child processes. Export substitutions or
    omitted committed files fail the original blob check, not silent normalization.
    """
    from hashlib import sha1
    selected = git('ls-files', '--stage', '-z', 'src', *SOURCE_EXTRA).decode().split('\0')
    selected = tuple(filter(None, selected))
    if not 1 <= len(selected) <= MAX_FILES:
        fail('source_inventory_invalid')
    raw = git('-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
              'archive', '--format=zip', 'HEAD', 'src', *SOURCE_EXTRA)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        total = 0
        for entry in selected:
            fields, name = entry.split('\t', 1)
            mode, expected, index = fields.split()
            clean_name(name)
            if mode != '100644' or index != '0': fail('source_mode_invalid')
            info = archive.getinfo(name)
            if not 0 <= info.file_size <= MAX_FILE: fail('file_too_large')
            with archive.open(info) as stream:
                data = stream.read(MAX_FILE + 1)
            total += len(data)
            if total > MAX_BYTES or len(data) != info.file_size: fail('source_bounds')
            if sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != expected:
                fail('source_changed')
            yield name, data


def build(source, output, allow_ci_build=False):
    """Copy only committed research source and a fresh CI-owned locked runtime."""
    if (allow_ci_build is not True or os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.name != 'nt' or sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8):
        fail('ci_build_only')
    source = source.resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), *args])
    if git('status', '--porcelain', '--untracked-files=all').strip():
        fail('dirty_source')
    commit = git('rev-parse', 'HEAD').decode().strip()
    tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
    lock = tomllib.loads((source/'uv.lock').read_text(encoding='utf-8'))
    locked = {p['name']: p['version'] for p in lock['package'] if 'version' in p}
    versions = {name: metadata.version(name) for name in DEPS}
    if any(versions[name] != locked[name] for name in DEPS):
        fail('unlocked_dependency')
    output = output.absolute(); output.mkdir(exist_ok=False)
    root = output/'payload'; root.mkdir()
    home = Path(sys.base_prefix).resolve()
    if not (home/'python.exe').is_file() or home == source or home.is_relative_to(source):
        fail('runtime_home_invalid')
    # uv's CI-owned standalone installation, including its licenses. Exclude
    # global site-packages/Scripts; only the named locked distributions follow.
    for name, path in walk(home).items():
        if name.lower().startswith(('lib/site-packages/', 'scripts/')) or '__pycache__' in Path(name).parts:
            continue
        target = root/'python'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file_bytes(path))
    for name in DEPS:
        dist = metadata.distribution(name)
        for entry in dist.files or ():
            rel = str(entry).replace('\\', '/')
            # Entry-point launchers point to the CI interpreter and are unused.
            if rel.startswith('../') or '__pycache__' in PurePosixPath(rel).parts or rel.endswith('.pyc'):
                continue
            clean_name(rel)
            if rel.endswith('.pth') or rel.endswith('direct_url.json'):
                fail('unexpected_dependency_path')
            data = file_bytes(Path(dist.locate_file(entry)))
            target = root/'python/Lib/site-packages'/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as dst: dst.write(data)
    for name, data in committed_source_files(git):
        target = root/'source'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (root/'probe-environment.py').write_bytes(git('show', 'HEAD:scripts/claude_probe_environment.py'))
    (root/'smoke.cmd').write_bytes(SMOKE_CMD)
    value = manifest(root, commit, tree, versions)
    (root/'environment-manifest.json').write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    verify(root)
    archive = output/'claude-probe-environment.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, path in sorted(walk(root).items()): z.write(path, name)
    digest = sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS').write_text(digest+'  '+archive.name+'\n', encoding='ascii')
    return dict(status='built_not_vendor_tested', sha256=digest, bytes=archive.stat().st_size,
                source_commit=commit, source_tree=tree, official_cli_included=False)


# --- Real Linux INPUT preparation (payload assembly; nothing executes) ------
_LINUX_BUILD_READY = (os.name == 'posix' and sys.version_info[:3] == (3, 12, 14)
                      and struct.calcsize('P') == 8)
LINUX_STDLIB_SKIP_DIRS = ('__pycache__', 'site-packages', 'dist-packages')


def _linux_measure_file(path):
    """Bounded read of a host source file; hardlinks allowed, links refused."""
    try:
        info = path.lstat()
    except OSError:
        fail('runtime_file_unavailable')
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        fail('payload_source_invalid')
    if info.st_size > MAX_FILE:
        fail('file_too_large')
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE + 1)
        after = os.fstat(stream.fileno())
    if len(data) != info.st_size or _identity(info) != _identity(after):
        fail('source_changed')
    return data


def _linux_dependency_distributions():
    """Installed lock-candidate distributions visible to this interpreter.

    Linux tuple: pytest's Linux-available closure plus tzdata (no system
    timezone data exists inside the namespace); colorama is a win32-marker
    dependency a correctly synced Linux venv never has.
    """
    for name in DEPS_LINUX:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            fail('dependency_missing')
        yield name, dist


def _linux_interpreter_layout():
    """Base CPython binary and stdlib of the running pinned interpreter.

    A virtualenv's own entry is never packaged: the base installation under
    sys.base_prefix is measured instead, so no venv link, pyvenv.cfg or host
    relative path can enter the payload.
    """
    import sysconfig
    binary = None
    for name in ('python3.12', 'python3'):
        candidate = Path(sys.base_prefix, 'bin', name)
        if candidate.is_file():
            binary = candidate.resolve()
            break
    if binary is None:
        binary = Path(sys.executable).resolve()
    return binary, Path(sysconfig.get_paths()['stdlib'])


def build_linux(source, destination):
    """Assemble a fresh symlink-free Linux INPUT payload; nothing executes.

    The payload contains python/bin/python3 (the pinned base CPython 3.12.14
    binary, mode 0755), the complete standard library including extension
    modules under python/lib/python3.12 (host caches and site/dist-packages
    excluded), lock-matched test dependencies under
    python/lib/python3.12/site-packages, and the committed source/tests the
    probe needs. No virtualenv metadata, editable install, HOME, .env,
    project .local, database or unrelated configuration is copied: the input
    set is exactly those closed lists. The environment manifest inventory
    (source commit/tree plus every payload file's hash and size) is generated
    and verified before returning.
    """
    if not _LINUX_BUILD_READY:
        fail('linux_build_host_unsupported')
    source = source.resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), *args])
    if git('status', '--porcelain', '--untracked-files=all').strip():
        fail('dirty_source')
    commit = git('rev-parse', 'HEAD').decode().strip()
    tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
    lock = tomllib.loads((source/'uv.lock').read_text(encoding='utf-8'))
    locked = {p['name']: p['version'] for p in lock['package'] if 'version' in p}
    distributions = list(_linux_dependency_distributions())
    versions = {name: dist.version for name, dist in distributions}
    if any(name not in locked or versions[name] != locked[name] for name in DEPS_LINUX):
        fail('unlocked_dependency')
    destination = destination.absolute()
    for parent in (destination.parent, *destination.parent.parents):
        plain(parent, directory=True)
    if os.path.lexists(destination):
        fail('destination_exists')
    binary, stdlib = _linux_interpreter_layout()
    if (not binary.is_file() or not stdlib.is_dir() or binary == source
            or binary.is_relative_to(source) or stdlib == source
            or stdlib.is_relative_to(source)):
        fail('runtime_home_invalid')
    destination.mkdir()
    (destination/'python/bin').mkdir(parents=True)
    _linux_exclusive_write(destination/'python/bin/python3',
                           _linux_measure_file(binary), 0o755)
    for name, path in sorted(walk(stdlib).items()):
        parts = PurePosixPath(name).parts
        if (any(part in LINUX_STDLIB_SKIP_DIRS for part in parts)
                or name.endswith('.pyc')):
            continue
        target = destination.joinpath('python', 'lib', 'python3.12', *parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(_linux_measure_file(path))
    for name, dist in distributions:
        for entry in dist.files or ():
            rel = str(entry).replace('\\', '/')
            # Launcher-style entry points, caches and any link back to this
            # host (pth, direct_url) never enter the payload.
            if (rel.startswith('../') or '__pycache__' in PurePosixPath(rel).parts
                    or rel.endswith('.pyc')):
                continue
            clean_name(rel)
            if rel.endswith('.pth') or rel.endswith('direct_url.json'):
                fail('unexpected_dependency_path')
            target = destination.joinpath('python', 'lib', 'python3.12',
                                          'site-packages', *PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(_linux_measure_file(Path(dist.locate_file(entry))))
    for name, data in committed_source_files(git):
        target = destination/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    value = manifest(destination, commit, tree, versions)
    (destination/'environment-manifest.json').write_text(
        json.dumps(value, indent=2)+'\n', encoding='utf-8')
    verify(destination)
    return dict(status='linux_input_built_not_executed', source_commit=commit,
                source_tree=tree, python=sys.version.split()[0],
                dependencies=versions, files=len(value['files']),
                official_cli_included=False, official_cli_executed=False,
                activation_authorized=False)


def _identity(info):
    """Identity tuple used by every official-generation boundary comparison."""
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _windows_path_problem(text):
    """Pure lexical classification of a production Windows path spelling."""
    if type(text) is not str or not text or len(text) > 4096:
        return 'not_a_bounded_string'
    if text.startswith('\\\\'):
        return 'unc_or_device_namespace'
    if any(c == '%' or ord(c) < 32 or ord(c) == 127 for c in text):
        return 'expansion_or_control'
    drive = re.match(r'[A-Za-z]:(.*)$', text, re.DOTALL)
    if drive is None or drive.group(1)[:1] not in ('\\', '/'):
        return 'not_drive_rooted'
    for part in re.split(r'[\\/]+', drive.group(1)):
        if not part:
            continue
        if part in ('.', '..'):
            return 'traversal_component'
        if re.search(r'[:*?"<>|]', part):
            return 'win32_forbidden_character'
        if part.endswith((' ', '.')):
            return 'trailing_dot_or_space'
        if part.split('.')[0].upper() in OFFICIAL_DEVICE_STEMS:
            return 'dos_device_name'
    return None


def _windows_local_drive(text):
    """Read-only drive-type query; production paths need a known local drive."""
    if os.name != 'nt':
        return False
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(text[:2] + '\\') == 3
    except Exception:
        return False


def _official_platform(value=None):
    """Validate an explicit preparation flavor token.

    None keeps the frozen host-dispatched historical behavior (Windows flavor
    with host-appropriate path spelling); 'windows'/'linux' select a flavor
    explicitly on any host.
    """
    if value is not None and value not in ('windows', 'linux'):
        fail('official_platform_unsupported')
    return value


def _official_path_argument(value, *, file=False, platform=None):
    """Lexically classify a supplied official path before any filesystem access."""
    _official_platform(platform)
    text = str(value)
    use_windows_lexical = platform == 'windows' or (platform is None and os.name == 'nt')
    if use_windows_lexical:
        if _windows_path_problem(text) is not None:
            fail('official_path_invalid')
        if not _windows_local_drive(text):
            fail('official_drive_unavailable')
    elif (not text.startswith('/') or len(text) > 4096
            or any(c == '%' or ord(c) < 32 or ord(c) == 127 for c in text)
            or any(part in ('', '.', '..') for part in text.split('/')[1:])):
        fail('official_path_invalid')
    path = Path(text)
    # The posix lexical branch above is already sufficient; the redundant host
    # backstop stays for the historical flavors exactly as reviewed.
    if platform != 'linux' and not path.is_absolute():
        fail('official_path_invalid')
    if file and path.suffix != ('.json' if platform == 'linux' else '.wsb'):
        fail('destination_suffix_invalid')
    return path


def _plain_ancestry(path):
    """Every selected parent must already exist as a plain directory."""
    try:
        for parent in (path.parent, *path.parent.parents):
            plain(parent, directory=True)
    except OSError:
        fail('ancestor_missing')


def _directory_chain(path):
    """Own identity plus plain ancestors; identity-aware alias detection."""
    own, ancestors = None, set()
    for index, node in enumerate((path, *path.parents)):
        try:
            identity = _identity(plain(node, directory=True))
        except (OSError, ValueError):
            continue
        if index == 0:
            own = identity
        else:
            ancestors.add(identity)
    return own, ancestors


def _mapping_spelling(path):
    """Case- and separator-normalized spelling for mapping overlap checks."""
    return os.path.normpath(str(path)).replace('\\', os.sep).replace('/', os.sep).casefold()


def _reject_mapping_overlap(*paths):
    """Refuse equal or nested mappings by spelling or directory identity.

    Identity comparison catches case and Windows short-name aliases of existing
    directories that spelling alone cannot; shared plain ancestors are allowed.
    """
    spellings = [_mapping_spelling(path) for path in paths]
    chains = [_directory_chain(path) for path in paths]
    for first in range(len(paths)):
        for second in range(first + 1, len(paths)):
            a, b = spellings[first], spellings[second]
            if a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep):
                fail('mapping_overlap')
            own_a, ancestors_a = chains[first]
            own_b, ancestors_b = chains[second]
            if own_a is not None and (own_a in ancestors_b or own_a == own_b):
                fail('mapping_overlap')
            if own_b is not None and own_b in ancestors_a:
                fail('mapping_overlap')


def _exclusive_write(path, data):
    """Exclusive creation only; a failed attempt is preserved, never retried."""
    with path.open('xb') as stream:
        stream.write(data)


def _bounded_image_digest(path, expected_bytes):
    """Bounded streamed length/digest; growth or truncation is refused."""
    if (type(expected_bytes) is not int
            or not 1 <= expected_bytes <= OFFICIAL_IMAGE_MAX_BYTES):
        fail('image_manifest_invalid')
    digest, read = sha256(), 0
    with path.open('rb') as stream:
        while block := stream.read(OFFICIAL_IMAGE_CHUNK):
            read += len(block)
            if read > expected_bytes:
                fail('image_size_mismatch')
            digest.update(block)
        after = os.fstat(stream.fileno())
    if read != expected_bytes:
        fail('image_size_mismatch')
    return digest.hexdigest(), _identity(after)


def _elf_read(stream, offset, size, limit):
    """One bounded seek/read; every span must fit inside the verified image."""
    if not 0 <= offset or not 1 <= size or offset + size > limit:
        fail('image_elf_invalid')
    if stream.seek(offset) != offset:
        fail('image_elf_invalid')
    data = stream.read(size)
    if len(data) != size:
        fail('image_elf_invalid')
    return data


def _elf_facts(path, size, require_interp=True):
    """Bounded seek-based ELF identity parse of an already-verified image.

    Returns the interpreter (None is permitted for shared objects when
    require_interp is False) and the deduplicated sorted DT_NEEDED closure,
    both derived from the file bytes. Nothing is resolved against host
    libraries here; host closure qualification is a separate later step.
    """
    before = plain(path)
    with path.open('rb') as stream:
        header = _elf_read(stream, 0, 64, size)
        if header[:4] != ELF_MAGIC or header[6] != 1:
            fail('image_elf_invalid')
        if header[4] != 2 or header[5] != 1:
            fail('image_arch_unsupported')
        (e_type, e_machine, _version, _entry, phoff, _shoff, _flags, _ehsize,
         phentsize, phnum) = struct.unpack_from('<HHIQQQIHHH', header, 16)
        if e_machine != 62:
            fail('image_arch_unsupported')
        if e_type not in (2, 3):
            fail('image_elf_invalid')
        if (phentsize != 56 or not 1 <= phnum <= ELF_MAX_PHDRS or phoff < 64
                or phoff + 56*phnum > size):
            fail('image_elf_invalid')
        phdrs = _elf_read(stream, phoff, 56*phnum, size)
        loads, interp, dynamic = [], None, None
        for index in range(phnum):
            (p_type, _p_flags, p_offset, p_vaddr, _p_paddr, p_filesz,
             _p_memsz, _p_align) = struct.unpack_from('<IIQQQQQQ', phdrs, 56*index)
            if p_offset > size or p_filesz > size or p_offset + p_filesz > size:
                fail('image_elf_invalid')
            if p_type == 1:
                loads.append((p_vaddr, p_offset, p_filesz))
            elif p_type == 3:
                if interp is not None or not 1 <= p_filesz <= ELF_MAX_INTERP_BYTES:
                    fail('image_elf_invalid')
                raw = _elf_read(stream, p_offset, p_filesz, size)
                if not raw.endswith(b'\0'):
                    fail('image_elf_invalid')
                try:
                    text = raw[:-1].decode('ascii')
                except UnicodeDecodeError:
                    fail('image_elf_invalid')
                if any(ord(c) < 33 or ord(c) > 126 for c in text):
                    fail('image_elf_invalid')
                interp = text
            elif p_type == 2:
                if (dynamic is not None or p_filesz == 0 or p_filesz % 16
                        or p_filesz > ELF_MAX_DYNAMIC_BYTES):
                    fail('image_elf_invalid')
                dynamic = (p_offset, p_filesz, p_vaddr)
        if interp is None and require_interp:
            fail('image_elf_invalid')
        if interp is not None and not interp.startswith('/'):
            fail('image_elf_invalid')
        needed_offsets, strtab_vaddr = [], None
        if dynamic is not None:
            raw = _elf_read(stream, dynamic[0], dynamic[1], size)
            for offset in range(0, len(raw) - 15, 16):
                tag, value = struct.unpack_from('<QQ', raw, offset)
                if tag == 0:
                    break
                if tag == 1:
                    needed_offsets.append(value)
                    if len(needed_offsets) > ELF_MAX_NEEDED:
                        fail('image_elf_invalid')
                elif tag == 5 and strtab_vaddr is None:
                    strtab_vaddr = value
                elif tag == 5:
                    fail('image_elf_invalid')
        needed = []
        if needed_offsets:
            if strtab_vaddr is None:
                fail('image_elf_invalid')
            span = next(((vaddr, offset, filesz) for vaddr, offset, filesz in loads
                         if vaddr <= strtab_vaddr < vaddr + filesz), None)
            if span is None:
                fail('image_elf_invalid')
            vaddr, offset, filesz = span
            start = offset + (strtab_vaddr - vaddr)
            limit = min(offset + filesz, start + ELF_MAX_STRTAB_BYTES)
            table = _elf_read(stream, start, limit - start, size)
            if not table.startswith(b'\0'):
                fail('image_elf_invalid')
            for position in needed_offsets:
                # DT_NEEDED holds an offset into the DT_STRTAB table itself.
                relative = position
                if not 0 < relative < len(table):
                    fail('image_elf_invalid')
                end = table.find(b'\0', relative)
                if end < 0 or end - relative > ELF_MAX_SONAME:
                    fail('image_elf_invalid')
                try:
                    name = table[relative:end].decode('ascii')
                except UnicodeDecodeError:
                    fail('image_elf_invalid')
                if any(ord(c) < 33 or ord(c) > 126 for c in name):
                    fail('image_elf_invalid')
                needed.append(name)
        after = os.fstat(stream.fileno())
    if (_identity(before) != _identity(after)
            or _identity(before) != _identity(plain(path))):
        fail('image_changed')
    return dict(interp=interp, needed=sorted(set(needed)))


def _load_official_image(image_dir, platform):
    """Exact inventory, bounded strict manifest, stable streamed hash/size.

    The Linux flavor additionally checks ELF/x86-64 structure and derives the
    runtime interpreter/library closure from the image bytes. sha256/bytes are
    always owner-supplied manifest values; this generator defaults nothing.
    """
    linux = platform == 'linux'
    member = LINUX_IMAGE_MEMBER if linux else OFFICIAL_IMAGE_MEMBER
    keys = LINUX_IMAGE_KEYS if linux else OFFICIAL_IMAGE_KEYS
    schema = LINUX_IMAGE_SCHEMA if linux else 'claude-probe-image-v1'
    try:
        plain(image_dir, directory=True)
        entries = sorted(os.listdir(image_dir))
    except OSError:
        fail('image_unavailable')
    if entries != sorted([member, OFFICIAL_MANIFEST_NAME]):
        fail('image_inventory_invalid')
    manifest_path = image_dir/OFFICIAL_MANIFEST_NAME
    if plain(manifest_path).st_size > OFFICIAL_MANIFEST_MAX_BYTES:
        fail('image_manifest_too_large')
    try:
        text = file_bytes(manifest_path).decode('ascii')
    except UnicodeDecodeError:
        fail('image_manifest_invalid')
    try:
        value = strict_json(text)
    except ValueError:
        fail('image_manifest_invalid')
    if (type(value) is not dict or set(value) != keys
            or value['schema'] != schema
            or value['path'] != member
            or type(value['sha256']) is not str
            or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None
            or type(value['bytes']) is not int
            or not 1 <= value['bytes'] <= OFFICIAL_IMAGE_MAX_BYTES
            or type(value['version']) is not str or value['version'] != OFFICIAL_IMAGE_VERSION
            or linux and value['platform'] != LINUX_IMAGE_PLATFORM):
        fail('image_manifest_invalid')
    image_path = image_dir/member
    before = plain(image_path)
    if before.st_size != value['bytes']:
        fail('image_size_mismatch')
    digest, after = _bounded_image_digest(image_path, value['bytes'])
    if digest != value['sha256']:
        fail('image_hash_mismatch')
    if _identity(before) != after or _identity(before) != _identity(plain(image_path)):
        fail('image_changed')
    if not linux:
        return value, {}
    return value, _elf_facts(image_path, value['bytes'])


def _official_image(image_dir):
    """Frozen historical Windows-image verification entry point."""
    return _load_official_image(image_dir, 'windows')[0]


def official_launcher(image_manifest, platform=None):
    """Pure deterministic launcher bytes; only digest and size vary."""
    if type(image_manifest) is not dict:
        fail('launcher_manifest_invalid')
    digest, size = image_manifest.get('sha256'), image_manifest.get('bytes')
    if (type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None
            or type(size) is not int or not 1 <= size <= OFFICIAL_IMAGE_MAX_BYTES):
        fail('launcher_manifest_invalid')
    if platform == 'linux':
        data = (LINUX_LAUNCHER_TEMPLATE
                .replace(b'{image_sha256}', digest.encode('ascii'))
                .replace(b'{image_bytes}', str(size).encode('ascii')))
        # POSIX sh legitimately uses ${...} expansion; only unfilled
        # substitution placeholders are refused.
        if (b'{image_sha256}' in data or b'{image_bytes}' in data or b'\r' in data
                or not data.startswith(b'#!/bin/sh\n')
                or any(len(line) >= 4096 for line in data.split(b'\n'))):
            fail('launcher_invalid')
        return data
    data = (OFFICIAL_LAUNCHER_TEMPLATE
            .replace(b'{image_sha256}', digest.encode('ascii'))
            .replace(b'{image_bytes}', str(size).encode('ascii')))
    if b'{' in data or any(len(line) >= 8191 for line in data.split(b'\r\n')):
        fail('launcher_invalid')
    return data


def _linux_launcher_mode_problem(mode):
    """The generated launcher carries exactly the reviewed 0755 mode bits."""
    if (mode & 0o7777) != 0o755:
        return 'launcher_mode_invalid'
    return None


def _linux_exclusive_write(path, data, mode):
    """Exclusive creation with an explicit POSIX mode; attempts are preserved."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
    descriptor = os.open(path, flags, mode)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
    finally:
        os.close(descriptor)
    if _LINUX_MODE_MEANINGFUL:
        os.chmod(path, mode)


def _official_control(control_dir, image_manifest, platform=None):
    """CONTROL must be exactly the generated launcher; anything else is refused."""
    linux = (platform or 'windows') == 'linux'
    name = LINUX_LAUNCHER_NAME if linux else OFFICIAL_LAUNCHER_NAME
    inventory = LINUX_CONTROL_INVENTORY if linux else OFFICIAL_CONTROL_INVENTORY
    try:
        plain(control_dir, directory=True)
        entries = sorted(os.listdir(control_dir))
    except OSError:
        fail('control_invalid')
    if entries != sorted(inventory):
        fail('control_invalid')
    launcher = control_dir/name
    data = file_bytes(launcher)
    if not data or data != official_launcher(image_manifest, platform='linux' if linux else None):
        fail('control_mismatch')
    if linux and _LINUX_MODE_MEANINGFUL:
        problem = _linux_launcher_mode_problem(stat.S_IMODE(plain(launcher).st_mode))
        if problem is not None:
            fail(problem)
    return data


def _official_payload_ready(value, platform=None):
    """The launcher needs manifest-inventoried payload layout members."""
    names = {entry['path'] for entry in value['files']}
    if (platform or 'windows') == 'linux':
        required = {'python/bin/python3',
                    'source/tests/test_research_claude_profile_native.py'}
        prefixes = ('source/', 'source/src/', 'python/lib/python3.12/site-packages/')
    else:
        required = {'python/python.exe',
                    'source/tests/test_research_claude_profile_native.py'}
        prefixes = ('source/', 'source/src/', 'python/Lib/site-packages/')
    if not required <= names:
        fail('payload_layout_unsupported')
    for prefix in prefixes:
        if not any(name.startswith(prefix) for name in names):
            fail('payload_layout_unsupported')


def official_sandbox_xml(input_dir, image_dir, control_dir, output_dir):
    """Four-mapping hardened Sandbox XML for the official probe run."""
    root = ET.Element('Configuration')
    for key, value in (('Networking', 'Disable'), ('ClipboardRedirection', 'Disable'),
            ('vGPU', 'Disable'), ('AudioInput', 'Disable'), ('VideoInput', 'Disable'),
            ('PrinterRedirection', 'Disable'), ('ProtectedClient', 'Enable'), ('MemoryInMB', '4096')):
        ET.SubElement(root, key).text = value
    mapped = ET.SubElement(root, 'MappedFolders')
    for host, guest, readonly in ((input_dir, r'C:\pal-input', 'true'),
                                 (image_dir, r'C:\pal-claude-image', 'true'),
                                 (control_dir, r'C:\pal-control', 'true'),
                                 (output_dir, r'C:\pal-output', 'false')):
        # Sandbox expands percent variables; XML escaping does not disable that.
        if '%' in str(host) or any(ord(c) < 32 for c in str(host)):
            fail('mapping_path_invalid')
        folder = ET.SubElement(mapped, 'MappedFolder')
        for key, value in (('HostFolder', str(host)), ('SandboxFolder', guest), ('ReadOnly', readonly)):
            ET.SubElement(folder, key).text = value
    command = ET.SubElement(root, 'LogonCommand')
    ET.SubElement(command, 'Command').text = (
        r'C:\Windows\System32\cmd.exe /d /c C:\pal-control\official-probe.cmd'
        r' --isolated-host-attested')
    return ET.tostring(root, encoding='ascii', xml_declaration=True)


def _linux_plan_flag_pairs(argv, flag):
    """(host, guest) pairs of a two-argument bind-style flag."""
    return {(argv[index+1], argv[index+2]) for index in range(len(argv) - 2)
            if argv[index] == flag}


def _linux_runtime_source(name):
    """Resolve an absolute interpreter path to its host location."""
    if os.path.isabs(name) and os.path.lexists(name):
        return Path(name)
    for directory in LINUX_RUNTIME_LIBRARY_DIRS:
        candidate = Path(directory, os.path.basename(name))
        if os.path.lexists(candidate):
            return candidate
    fail('runtime_closure_incomplete')


def _linux_soname_location(name):
    """First canonical directory of the pinned search order providing name."""
    for directory in LINUX_RUNTIME_LIBRARY_DIRS:
        if os.path.lexists(Path(directory, name)):
            return f'{directory}/{name}'
    fail('runtime_closure_incomplete')


def _linux_runtime_closure(payload_root, payload_names, facts):
    """Resolve, measure and pin the recursive guest runtime closure.

    A1 record: the v2 launcher invokes no external command, so the closure
    roots are exactly the official image ELF (interpreter plus DT_NEEDED
    derived from the verified image bytes), host /bin/sh, the payload
    interpreter python/bin/python3, and every packaged *.so (their loader
    dependencies). Each resolved file is bound read-only at its canonical
    guest path - ld.so at its PT_INTERP path, sonames at the first directory
    of the pinned search order providing them, /bin/sh at /bin/sh - and
    LD_LIBRARY_PATH is not used. Every hash and size is measured from the
    host bytes; nothing is defaulted or invented.
    """
    binds, parsed, pending = {}, set(), []
    def bind(guest, source):
        real = Path(os.path.realpath(str(source)))
        data = _linux_measure_file(real)
        digest = sha256(data).hexdigest()
        previous = binds.get(guest)
        if previous is not None:
            if previous['source'] != str(real) or previous['sha256'] != digest:
                fail('runtime_bind_conflict')
            return
        if len(binds) >= LINUX_MAX_RUNTIME_BINDS:
            fail('runtime_closure_unbounded')
        binds[guest] = dict(guest=guest, mode='ro', source=str(real),
                            sha256=digest, bytes=len(data))
        pending.append(real)
    def parse(real):
        if str(real) in parsed:
            return
        parsed.add(str(real))
        data = _linux_measure_file(real)
        facts_here = _elf_facts(real, len(data), require_interp=False)
        if facts_here['interp'] is not None:
            bind(facts_here['interp'], _linux_runtime_source(facts_here['interp']))
        for name in facts_here['needed']:
            location = _linux_soname_location(name)
            bind(location, Path(location))
    bind(facts['interp'], _linux_runtime_source(facts['interp']))
    for name in facts['needed']:
        location = _linux_soname_location(name)
        bind(location, Path(location))
    bind(LINUX_GUEST_SHELL, LINUX_SHELL_HOST_PATH)
    bind(LINUX_GUESTS['input']+'/python/bin/python3', payload_root/'python/bin/python3')
    for name in sorted(payload_names):
        if name.startswith('python/') and name.endswith('.so'):
            pending.append(payload_root.joinpath(*PurePosixPath(name).parts))
    while pending:
        parse(pending.pop())
    return [binds[guest] for guest in sorted(binds)]


def _linux_namespace_plan_problem(plan):
    """Self-check the generated v2 launch plan before it is ever written.

    Executor-facing invariants: v1 generation-only schemas are rejected;
    bwrap 0.11.1 --size/--tmpfs spelling (no --sizelimit); every runtime bind
    enumerated, measured and consistent with argv; NO writable host bind
    anywhere (the OUTPUT argument is a host export destination crossed only
    through the bounded /pal-output tmpfs); explicit clean environment, not a
    bare --clearenv; no ip command (loopback is automatic under --unshare-net);
    pinned two-mode launcher contract; pinned resource bounds; no execution
    claims. A tampered or weakened plan is refused instead of emitted.
    """
    if (type(plan) is not dict or plan.get('schema') != LINUX_PLAN_SCHEMA
            or plan.get('generation') != 'config_only_not_executed'):
        return 'namespace_plan_invalid'
    if sorted(plan.get('namespaces') or ()) != sorted(LINUX_NAMESPACES):
        return 'namespace_plan_invalid'
    runner = plan.get('runner')
    if (type(runner) is not dict
            or sorted(runner) != ['bwrap_version', 'execution', 'supervision']
            or runner.get('bwrap_version') != LINUX_BWRAP_VERSION
            or runner.get('execution') != 'outer_runner_owned_separately'
            or runner.get('supervision') != 'outside_workload_cgroup'):
        return 'namespace_plan_invalid'
    network = plan.get('network')
    if (type(network) is not dict
            or sorted(network) != ['address', 'external_egress', 'loopback', 'mode']
            or network.get('mode') != 'loopback_only'
            or network.get('external_egress') != 'unavailable'
            or network.get('address') != '127.0.0.1'
            or network.get('loopback') != LINUX_LOOPBACK_MODE):
        return 'namespace_plan_invalid'
    image = plan.get('image')
    if (type(image) is not dict or sorted(image) != ['bytes', 'closure_derived_from',
            'member', 'platform', 'runtime_interp', 'runtime_needed', 'sha256',
            'version'] or image.get('closure_derived_from') != 'image_bytes'
            or image.get('member') != LINUX_IMAGE_MEMBER
            or image.get('platform') != LINUX_IMAGE_PLATFORM
            or image.get('version') != OFFICIAL_IMAGE_VERSION
            or type(image.get('sha256')) is not str
            or re.fullmatch('[0-9a-f]{64}', image.get('sha256') or '') is None
            or type(image.get('bytes')) is not int
            or not 1 <= image['bytes'] <= OFFICIAL_IMAGE_MAX_BYTES
            or type(image.get('runtime_interp')) is not str
            or not image['runtime_interp'].startswith('/')
            or any(ord(c) < 33 or ord(c) > 126 for c in image['runtime_interp'])):
        return 'namespace_plan_invalid'
    needed = image.get('runtime_needed')
    if type(needed) is not list or not 0 <= len(needed) <= ELF_MAX_NEEDED:
        return 'namespace_plan_invalid'
    for name in needed:
        if (type(name) is not str or not name or len(name) > ELF_MAX_SONAME
                or any(ord(c) < 33 or ord(c) > 126 for c in name)):
            return 'namespace_plan_invalid'
    if needed != sorted(set(needed)):
        return 'namespace_plan_invalid'
    argv = plan.get('argv')
    if (type(argv) is not list or len(argv) < 8 or argv[0] != 'bwrap'
            or any(type(item) is not str or not item for item in argv)):
        return 'namespace_plan_invalid'
    # No flag outside the approved v2 set may appear before the final command.
    # Writable host binds (--bind/--dev-bind/--bind-try/...) and the removed
    # --sizelimit spelling are refused even when flag counts stay intact.
    approved = {'--unshare-user', '--unshare-ipc', '--unshare-pid',
                '--unshare-net', '--unshare-uts', '--die-with-parent',
                '--new-session', '--cap-drop', '--clearenv', '--setenv',
                '--dev', '--proc', '--ro-bind', '--tmpfs', '--size'}
    if any(item.startswith('--') and item not in approved for item in argv[:-2]):
        return 'namespace_plan_invalid'
    for flag in ('--unshare-user', '--unshare-ipc', '--unshare-pid',
                 '--unshare-net', '--unshare-uts', '--die-with-parent',
                 '--new-session', '--clearenv', '--dev', '--proc'):
        if argv.count(flag) != 1:
            return 'namespace_plan_invalid'
    for flag, operand in (('--dev', '/dev'), ('--proc', '/proc')):
        if not any(argv[index:index+2] == [flag, operand]
                   for index in range(len(argv) - 1)):
            return 'namespace_plan_invalid'
    if ('--cap-drop' not in argv
            or any(argv[index] == '--cap-drop' and argv[index+1] != 'ALL'
                   for index in range(len(argv) - 1))):
        return 'namespace_plan_invalid'
    environment = plan.get('environment')
    if (type(environment) is not dict
            or sorted(environment) != ['clearenv', 'setenv']
            or environment.get('clearenv') is not True
            or environment.get('setenv') != LINUX_CHILD_ENVIRONMENT):
        return 'namespace_plan_invalid'
    if _linux_plan_flag_pairs(argv, '--setenv') != set(LINUX_CHILD_ENVIRONMENT.items()):
        return 'namespace_plan_invalid'
    if argv.count('--tmpfs') != 4 or argv.count('--size') != 3:
        return 'namespace_plan_invalid'
    if not any(argv[index:index+2] == ['--tmpfs', '/']
               for index in range(len(argv) - 1)):
        return 'namespace_plan_invalid'
    # Every sized tmpfs must spell bwrap 0.11.1's --size N --tmpfs PATH; a
    # dropped, moved, inflated or detached size bound is refused.
    for sequence in (('--size', str(LINUX_SCRATCH_BYTES), '--tmpfs', LINUX_GUESTS['scratch']),
                     ('--size', str(LINUX_TMP_BYTES), '--tmpfs', LINUX_GUESTS['tmp']),
                     ('--size', str(LINUX_EXPORT_BYTES), '--tmpfs', LINUX_GUESTS['output'])):
        if not any(tuple(argv[index:index+4]) == sequence
                   for index in range(len(argv) - 3)):
            return 'namespace_plan_invalid'
    mounts = plan.get('mounts')
    if type(mounts) is not list or len(mounts) != 6:
        return 'namespace_plan_invalid'
    order = ('INPUT', 'IMAGE', 'CONTROL', 'OUTPUT', 'SCRATCH', 'TMP')
    readonlys = {'INPUT': True, 'IMAGE': True, 'CONTROL': True,
                 'OUTPUT': False, 'SCRATCH': False, 'TMP': False}
    kinds = {'INPUT': 'bind', 'IMAGE': 'bind', 'CONTROL': 'bind',
             'OUTPUT': 'tmpfs', 'SCRATCH': 'tmpfs', 'TMP': 'tmpfs'}
    sizes = {'OUTPUT': LINUX_EXPORT_BYTES, 'SCRATCH': LINUX_SCRATCH_BYTES,
             'TMP': LINUX_TMP_BYTES}
    hosts = {}
    for index, mount in enumerate(mounts):
        if type(mount) is not dict or mount.get('role') != order[index]:
            return 'namespace_plan_invalid'
        role = mount['role']
        keys = {'role', 'host', 'guest', 'readonly', 'kind'}
        if role in sizes:
            keys.add('size_limit_bytes')
        if role == 'OUTPUT':
            keys.add('host_role')
        if (set(mount) != keys or mount['kind'] != kinds[role]
                or mount['readonly'] is not readonlys[role]
                or mount['guest'] != LINUX_GUESTS[role.lower()]):
            return 'namespace_plan_invalid'
        if role == 'OUTPUT':
            if (mount['host_role'] != 'export_destination'
                    or mount['size_limit_bytes'] != sizes[role]
                    or type(mount['host']) is not str or not mount['host']):
                return 'namespace_plan_invalid'
        elif role in sizes:
            if mount['host'] is not None or mount['size_limit_bytes'] != sizes[role]:
                return 'namespace_plan_invalid'
        elif (type(mount['host']) is not str or not mount['host']
                or '\0' in mount['host']):
            return 'namespace_plan_invalid'
        hosts[role] = mount['host']
    export = plan.get('export')
    if (type(export) is not dict
            or sorted(export) != ['bounded_bytes', 'creation', 'destination',
                                  'mounted_writable_in_namespace']
            or export.get('destination') != hosts.get('OUTPUT')
            or export.get('bounded_bytes') != LINUX_EXPORT_BYTES
            or export.get('creation') != 'exclusive_no_follow'
            or export.get('mounted_writable_in_namespace') is not False):
        return 'namespace_plan_invalid'
    # The CONTROL launcher identity is REQUIRED and must match the
    # deterministic launcher recomputed from the already-validated image
    # identity (pure derivation, no filesystem access); an absent, altered
    # or misdirected block is refused so a host-level launcher swap between
    # generation and execution is detectable at admission.
    launcher = plan.get('launcher')
    if type(launcher) is not dict or sorted(launcher) != ['bytes', 'path', 'sha256']:
        return 'namespace_plan_invalid'
    expected_launcher = official_launcher(dict(sha256=image.get('sha256'),
                                               bytes=image.get('bytes')), platform='linux')
    if (launcher.get('path') != hosts.get('CONTROL')+'/'+LINUX_LAUNCHER_NAME
            or launcher.get('sha256') != sha256(expected_launcher).hexdigest()
            or launcher.get('bytes') != len(expected_launcher)):
        return 'namespace_plan_invalid'
    binds = plan.get('runtime_binds')
    if type(binds) is not list or not 1 <= len(binds) <= LINUX_MAX_RUNTIME_BINDS:
        return 'namespace_plan_invalid'
    seen_guests, seen_sources, pairs = set(), set(), set()
    for bind in binds:
        if (type(bind) is not dict
                or sorted(bind) != ['bytes', 'guest', 'mode', 'sha256', 'source']
                or bind.get('mode') != 'ro'
                or type(bind.get('guest')) is not str or not bind['guest']
                or type(bind.get('source')) is not str or not bind['source']
                or '\0' in bind['guest'] or '\0' in bind['source']
                or type(bind.get('sha256')) is not str
                or re.fullmatch('[0-9a-f]{64}', bind['sha256']) is None
                or type(bind.get('bytes')) is not int
                or not 1 <= bind['bytes'] <= MAX_FILE):
            return 'namespace_plan_invalid'
        if bind['guest'] in seen_guests or bind['source'] in seen_sources:
            return 'namespace_plan_invalid'
        seen_guests.add(bind['guest'])
        seen_sources.add(bind['source'])
        pairs.add((bind['source'], bind['guest']))
    layout = plan.get('runtime_layout')
    if (type(layout) is not dict
            or sorted(layout) != ['guest_paths', 'launcher_externals',
                                  'ld_library_path', 'library_search',
                                  'shell_guest', 'shell_source']
            or layout.get('guest_paths') != 'canonical'
            or layout.get('ld_library_path') != 'not_used'
            or layout.get('launcher_externals') != 'shell_builtins_and_payload_python_only'
            or layout.get('library_search') != list(LINUX_RUNTIME_LIBRARY_DIRS)
            or layout.get('shell_guest') != LINUX_GUEST_SHELL
            or type(layout.get('shell_source')) is not str):
        return 'namespace_plan_invalid'
    shell = next((bind for bind in binds if bind['guest'] == LINUX_GUEST_SHELL), None)
    if shell is None or shell['source'] != layout['shell_source']:
        return 'namespace_plan_invalid'
    expected = {(hosts['INPUT'], LINUX_GUESTS['input']),
                (hosts['IMAGE'], LINUX_GUESTS['image']),
                (hosts['CONTROL'], LINUX_GUESTS['control'])} | pairs
    if _linux_plan_flag_pairs(argv, '--ro-bind') != expected:
        return 'namespace_plan_invalid'
    if argv.count('--ro-bind') != 3 + len(binds):
        return 'namespace_plan_invalid'
    modes = plan.get('modes')
    if type(modes) is not list or len(modes) != 2:
        return 'namespace_plan_invalid'
    qualify, batch = modes
    mode_keys = ['command', 'depends_on', 'expected_banner', 'mode',
                 'selection', 'synthetic_request']
    if (type(qualify) is not dict or sorted(qualify) != mode_keys
            or qualify != dict(mode='qualify-version',
                               selection='outer_runner_final_command_replacement',
                               command=[LINUX_GUESTS['image']+'/'+LINUX_IMAGE_MEMBER,
                                        '--version'],
                               expected_banner=image.get('version')+' (Claude Code)',
                               synthetic_request=False, depends_on=[])):
        return 'namespace_plan_invalid'
    if (type(batch) is not dict or sorted(batch) != mode_keys
            or batch != dict(mode='official-six', selection='plan_argv_final_command',
                             command=[LINUX_GUESTS['control']+'/'+LINUX_LAUNCHER_NAME,
                                      '--isolated-host-attested'],
                             expected_banner=None, synthetic_request=True,
                             depends_on=['qualify-version'])):
        return 'namespace_plan_invalid'
    if argv[-2:] != batch['command']:
        return 'namespace_plan_invalid'
    # Loopback comes up automatically under --unshare-net; the ip command is
    # neither bound nor invoked anywhere in the launch plan.
    if any(item == 'ip' or item.startswith('ip ') for item in argv):
        return 'namespace_plan_invalid'
    if sorted(plan.get('excluded_host_surfaces') or ()) != sorted(LINUX_EXCLUDED_SURFACES):
        return 'namespace_plan_invalid'
    bounds = plan.get('bounds')
    if (type(bounds) is not dict
            or sorted(bounds) != ['cgroup_controls', 'deadline_seconds', 'memory_mb',
                                  'memory_swap_max', 'pids_max']
            or bounds.get('memory_mb') != LINUX_MEMORY_MB
            or bounds.get('memory_swap_max') != 0
            or bounds.get('pids_max') != LINUX_PIDS_MAX
            or bounds.get('deadline_seconds') != LINUX_DEADLINE_SECONDS
            or bounds.get('cgroup_controls') != 'require_qualification_before_run'):
        return 'namespace_plan_invalid'
    if (plan.get('official_cli_executed') is not False
            or plan.get('activation_authorized') is not False):
        return 'namespace_plan_invalid'
    return None


def _linux_namespace_plan(payload_root, payload_value, image_dir, control_dir,
                          output_dir, value, facts):
    """Deterministic rootless bwrap launch plan; generation output, never run.

    A2 record: --tmpfs / gives a fresh empty guest root (the host root is
    excluded, not merely unlisted); INPUT/IMAGE/CONTROL are read-only binds;
    /pal-scratch, /tmp and /pal-output are sized tmpfs mounts using bwrap
    0.11.1's --size N --tmpfs PATH spelling; every runtime file (ld.so,
    DT_NEEDED closures, /bin/sh, the payload interpreter's loader needs) is
    enumerated as a measured read-only bind at its canonical guest path. The
    --output-dir argument is the HOST EXPORT DESTINATION: bounded 64 MiB,
    created exclusively without following symlinks by the outer runner, and
    NEVER mounted writable into the namespace - output crosses only through
    the bounded /pal-output tmpfs. A3 record: the two fixed launcher modes
    are pinned below as plan data read by the separately owned outer runner;
    the launcher file itself is mode-independent. qualify-version replaces
    the final argv command with one official --version invocation before the
    pytest entry and gates official-six, which uses the generated final
    command unchanged. The launcher identity block pins the deterministic
    CONTROL launcher by the exact bytes written (their on-disk equality was
    verified by _official_control at generation time), so a host-level swap
    between generation and execution is detectable at admission.
    """
    payload_names = [entry['path'] for entry in payload_value['files']]
    runtime_binds = _linux_runtime_closure(payload_root, payload_names, facts)
    launcher_data = official_launcher(value, platform='linux')
    argv = ['bwrap', '--unshare-user', '--unshare-ipc', '--unshare-pid',
            '--unshare-net', '--unshare-uts', '--die-with-parent', '--new-session',
            '--cap-drop', 'ALL', '--clearenv',
            '--setenv', 'PATH', LINUX_CHILD_ENVIRONMENT['PATH'],
            '--tmpfs', '/', '--dev', '/dev', '--proc', '/proc',
            '--ro-bind', str(payload_root), LINUX_GUESTS['input'],
            '--ro-bind', str(image_dir), LINUX_GUESTS['image'],
            '--ro-bind', str(control_dir), LINUX_GUESTS['control'],
            '--size', str(LINUX_SCRATCH_BYTES), '--tmpfs', LINUX_GUESTS['scratch'],
            '--size', str(LINUX_TMP_BYTES), '--tmpfs', LINUX_GUESTS['tmp'],
            '--size', str(LINUX_EXPORT_BYTES), '--tmpfs', LINUX_GUESTS['output'],
            *(part for entry in runtime_binds
              for part in ('--ro-bind', entry['source'], entry['guest'])),
            LINUX_GUESTS['control']+'/'+LINUX_LAUNCHER_NAME, '--isolated-host-attested']
    plan = dict(
        schema=LINUX_PLAN_SCHEMA, generation='config_only_not_executed',
        runner=dict(bwrap_version=LINUX_BWRAP_VERSION,
                    execution='outer_runner_owned_separately',
                    supervision='outside_workload_cgroup'),
        image=dict(sha256=value['sha256'], bytes=value['bytes'],
                   version=value['version'], platform=LINUX_IMAGE_PLATFORM,
                   member=LINUX_IMAGE_MEMBER, runtime_interp=facts['interp'],
                   runtime_needed=list(facts['needed']),
                   closure_derived_from='image_bytes'),
        namespaces=list(LINUX_NAMESPACES),
        network=dict(mode='loopback_only', external_egress='unavailable',
                     address='127.0.0.1', loopback=LINUX_LOOPBACK_MODE),
        mounts=[dict(role='INPUT', host=str(payload_root), guest=LINUX_GUESTS['input'],
                     readonly=True, kind='bind'),
                dict(role='IMAGE', host=str(image_dir), guest=LINUX_GUESTS['image'],
                     readonly=True, kind='bind'),
                dict(role='CONTROL', host=str(control_dir), guest=LINUX_GUESTS['control'],
                     readonly=True, kind='bind'),
                dict(role='OUTPUT', host=str(output_dir), guest=LINUX_GUESTS['output'],
                     readonly=False, kind='tmpfs', size_limit_bytes=LINUX_EXPORT_BYTES,
                     host_role='export_destination'),
                dict(role='SCRATCH', host=None, guest=LINUX_GUESTS['scratch'],
                     readonly=False, kind='tmpfs', size_limit_bytes=LINUX_SCRATCH_BYTES),
                dict(role='TMP', host=None, guest=LINUX_GUESTS['tmp'],
                     readonly=False, kind='tmpfs', size_limit_bytes=LINUX_TMP_BYTES)],
        export=dict(destination=str(output_dir), bounded_bytes=LINUX_EXPORT_BYTES,
                    creation='exclusive_no_follow',
                    mounted_writable_in_namespace=False),
        launcher=dict(path=str(control_dir)+'/'+LINUX_LAUNCHER_NAME,
                      sha256=sha256(launcher_data).hexdigest(), bytes=len(launcher_data)),
        runtime_binds=runtime_binds,
        runtime_layout=dict(guest_paths='canonical', ld_library_path='not_used',
                            library_search=list(LINUX_RUNTIME_LIBRARY_DIRS),
                            launcher_externals='shell_builtins_and_payload_python_only',
                            shell_guest=LINUX_GUEST_SHELL,
                            shell_source=next(entry['source'] for entry in runtime_binds
                                              if entry['guest'] == LINUX_GUEST_SHELL)),
        environment=dict(clearenv=True, setenv=dict(LINUX_CHILD_ENVIRONMENT)),
        modes=[dict(mode='qualify-version',
                    selection='outer_runner_final_command_replacement',
                    command=[LINUX_GUESTS['image']+'/'+LINUX_IMAGE_MEMBER, '--version'],
                    expected_banner=value['version']+' (Claude Code)',
                    synthetic_request=False, depends_on=[]),
               dict(mode='official-six', selection='plan_argv_final_command',
                    command=[LINUX_GUESTS['control']+'/'+LINUX_LAUNCHER_NAME,
                             '--isolated-host-attested'],
                    expected_banner=None, synthetic_request=True,
                    depends_on=['qualify-version'])],
        excluded_host_surfaces=list(LINUX_EXCLUDED_SURFACES),
        argv=argv,
        bounds=dict(memory_mb=LINUX_MEMORY_MB, memory_swap_max=0,
                    pids_max=LINUX_PIDS_MAX, deadline_seconds=LINUX_DEADLINE_SECONDS,
                    cgroup_controls='require_qualification_before_run'),
        official_cli_executed=False, activation_authorized=False)
    problem = _linux_namespace_plan_problem(plan)
    if problem is not None:
        fail(problem)
    return plan


def official_control(image_dir, destination, *, platform=None):
    """Validate IMAGE, exclusively create CONTROL, write the launcher; no launch."""
    _official_platform(platform)
    return _official_control_generate(
        _official_path_argument(image_dir, platform=platform),
        _official_path_argument(destination, platform=platform), platform)


def _official_control_generate(image_dir, destination, platform):
    """Generation core operating on already-classified path arguments."""
    linux = (platform or 'windows') == 'linux'
    _plain_ancestry(image_dir)
    value, facts = _load_official_image(image_dir, 'linux' if linux else 'windows')
    _plain_ancestry(destination)
    if os.path.lexists(destination):
        fail('destination_exists')
    _reject_mapping_overlap(image_dir, destination)
    launcher = official_launcher(value, platform='linux' if linux else None)
    try:
        destination.mkdir()
    except FileExistsError:
        fail('destination_exists')
    plain(destination, directory=True)
    _reject_mapping_overlap(image_dir, destination)
    if linux:
        _linux_exclusive_write(destination/LINUX_LAUNCHER_NAME, launcher, 0o755)
        return dict(status='official_control_generated_not_launched',
                    image_sha256=value['sha256'], image_bytes=value['bytes'],
                    image_version=value['version'], image_platform=LINUX_IMAGE_PLATFORM,
                    runtime_interp=facts['interp'], runtime_needed=facts['needed'],
                    official_cli_executed=False, activation_authorized=False)
    _exclusive_write(destination/OFFICIAL_LAUNCHER_NAME, launcher)
    return dict(status='official_control_generated_not_launched',
                image_sha256=value['sha256'], image_bytes=value['bytes'],
                image_version=value['version'], official_cli_executed=False,
                activation_authorized=False)


def official_config(payload_root, image_dir, control_dir, output_dir, destination,
                    *, isolated_host_attested=False, platform=None):
    """Coordinate validations, then exclusively create OUTPUT and the config."""
    if isolated_host_attested is not True:
        fail('isolated_host_attestation_required')
    _official_platform(platform)
    payload_root = _official_path_argument(payload_root, platform=platform)
    image_dir = _official_path_argument(image_dir, platform=platform)
    control_dir = _official_path_argument(control_dir, platform=platform)
    output_dir = _official_path_argument(output_dir, platform=platform)
    destination = _official_path_argument(destination, file=True, platform=platform)
    return _official_config_generate(payload_root, image_dir, control_dir,
                                     output_dir, destination, platform)


def _official_config_generate(payload_root, image_dir, control_dir, output_dir,
                              destination, platform):
    """Generation core operating on already-classified path arguments."""
    linux = (platform or 'windows') == 'linux'
    flavor = 'linux' if linux else 'windows'
    _plain_ancestry(payload_root)
    payload_value = verify(payload_root)
    _official_payload_ready(payload_value, platform=flavor)
    _plain_ancestry(image_dir)
    value, facts = _load_official_image(image_dir, flavor)
    launcher = official_launcher(value, platform=flavor)
    _plain_ancestry(control_dir)
    _official_control(control_dir, value, platform=flavor)
    _plain_ancestry(output_dir)
    if os.path.lexists(output_dir):
        fail('output_dir_exists')
    _plain_ancestry(destination)
    if os.path.lexists(destination):
        fail('destination_exists')
    _reject_mapping_overlap(payload_root, image_dir, control_dir, output_dir,
                            destination)
    # The Linux launch plan (including the measured runtime closure) is fully
    # self-validated before the export destination directory is created.
    if linux:
        plan = _linux_namespace_plan(payload_root, payload_value, image_dir,
                                     control_dir, output_dir, value, facts)
        data = (json.dumps(plan, indent=2, sort_keys=True) + '\n').encode('ascii')
    try:
        output_dir.mkdir()
    except FileExistsError:
        fail('output_dir_exists')
    plain(output_dir, directory=True)
    _reject_mapping_overlap(payload_root, image_dir, control_dir, output_dir)
    _reject_mapping_overlap(output_dir, destination)
    if linux:
        _exclusive_write(destination, data)
        return dict(status='official_config_generated_not_launched',
                    schema=LINUX_PLAN_SCHEMA,
                    modes=[mode['mode'] for mode in plan['modes']],
                    runtime_binds=len(plan['runtime_binds']),
                    image_sha256=value['sha256'], image_bytes=value['bytes'],
                    image_version=value['version'], image_platform=LINUX_IMAGE_PLATFORM,
                    runtime_interp=facts['interp'], runtime_needed=facts['needed'],
                    namespaces=list(LINUX_NAMESPACES),
                    official_cli_executed=False, activation_authorized=False)
    _exclusive_write(destination, official_sandbox_xml(payload_root, image_dir,
                                                       control_dir, output_dir))
    return dict(status='official_config_generated_not_launched',
                image_sha256=value['sha256'], image_bytes=value['bytes'],
                image_version=value['version'], official_cli_executed=False,
                activation_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for op in ('verify', 'selftest'):
        p = sub.add_parser(op); p.add_argument('--root', type=Path, required=True)
        if op == 'selftest': p.add_argument('--receipt', type=Path, required=True)
    p = sub.add_parser('stage'); p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--sha256', required=True); p.add_argument('--destination', type=Path, required=True)
    p = sub.add_parser('build'); p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--allow-ci-build', action='store_true')
    p = sub.add_parser('build-linux', allow_abbrev=False)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p = sub.add_parser('official-control', allow_abbrev=False)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--platform', choices=('windows', 'linux'))
    p = sub.add_parser('official-config', allow_abbrev=False)
    p.add_argument('--payload-root', type=Path, required=True)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--control-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--isolated-host-attested', action='store_true')
    p.add_argument('--platform', choices=('windows', 'linux'))
    args = parser.parse_args()
    try:
        if args.command == 'build': result = build(args.source, args.output, args.allow_ci_build)
        elif args.command == 'build-linux': result = build_linux(args.source, args.destination)
        elif args.command == 'stage': result = stage(args.archive, args.sha256, args.destination)
        elif args.command == 'selftest': result = selftest(args.root, args.receipt)
        elif args.command == 'official-control':
            result = official_control(args.image_dir, args.destination,
                                      platform=args.platform)
        elif args.command == 'official-config':
            result = official_config(args.payload_root, args.image_dir, args.control_dir,
                                     args.output_dir, args.destination,
                                     isolated_host_attested=args.isolated_host_attested,
                                     platform=args.platform)
        else:
            value = verify(args.root)
            result = dict(status='verified_not_activated', source_commit=value['source_commit'])
        print(json.dumps(result, sort_keys=True)); return 0
    except Exception as error:
        # No exception text, paths, environment or source data in public output.
        code = error.args[0] if type(error) is ValueError and len(error.args) == 1 else 'preparation_failed'
        if type(code) is not str or not re.fullmatch('[a-z_]{1,64}', code): code = 'preparation_failed'
        print(json.dumps(dict(status='BLOCKED', reason=code, activation_authorized=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
