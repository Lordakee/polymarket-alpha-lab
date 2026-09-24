"""Offline TEST packaging/preparation plus official-run CONFIG GENERATION.

Preparation modes (build/stage/verify/selftest) keep their reviewed behavior
and never launch a vendor CLI. The official-control/official-config generators
likewise execute no program: they only validate reviewed inputs and write the
control launcher and a separate four-mapping .wsb. OPENING that generated
configuration is what runs the official launcher inside Windows Sandbox.
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
DEPS = ('pytest', 'tzdata', 'colorama', 'iniconfig', 'packaging', 'pluggy', 'pygments')
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


def _official_path_argument(value, *, file=False):
    """Lexically classify a supplied official path before any filesystem access."""
    text = str(value)
    if os.name == 'nt':
        if _windows_path_problem(text) is not None:
            fail('official_path_invalid')
        if not _windows_local_drive(text):
            fail('official_drive_unavailable')
    elif (not text.startswith('/') or len(text) > 4096
            or any(c == '%' or ord(c) < 32 or ord(c) == 127 for c in text)
            or any(part in ('', '.', '..') for part in text.split('/')[1:])):
        fail('official_path_invalid')
    path = Path(text)
    if not path.is_absolute():
        fail('official_path_invalid')
    if file and path.suffix != '.wsb':
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


def _official_image(image_dir):
    """Exact inventory, bounded strict manifest, stable streamed hash/size."""
    try:
        plain(image_dir, directory=True)
        entries = sorted(os.listdir(image_dir))
    except OSError:
        fail('image_unavailable')
    if entries != sorted(OFFICIAL_IMAGE_INVENTORY):
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
    if (type(value) is not dict or set(value) != OFFICIAL_IMAGE_KEYS
            or value['schema'] != 'claude-probe-image-v1'
            or value['path'] != OFFICIAL_IMAGE_MEMBER
            or type(value['sha256']) is not str
            or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None
            or type(value['bytes']) is not int
            or not 1 <= value['bytes'] <= OFFICIAL_IMAGE_MAX_BYTES
            or type(value['version']) is not str or value['version'] != OFFICIAL_IMAGE_VERSION):
        fail('image_manifest_invalid')
    image_path = image_dir/OFFICIAL_IMAGE_MEMBER
    before = plain(image_path)
    if before.st_size != value['bytes']:
        fail('image_size_mismatch')
    digest, after = _bounded_image_digest(image_path, value['bytes'])
    if digest != value['sha256']:
        fail('image_hash_mismatch')
    if _identity(before) != after or _identity(before) != _identity(plain(image_path)):
        fail('image_changed')
    return value


def official_launcher(image_manifest):
    """Pure deterministic ASCII/CRLF launcher; only digest and size vary."""
    if type(image_manifest) is not dict:
        fail('launcher_manifest_invalid')
    digest, size = image_manifest.get('sha256'), image_manifest.get('bytes')
    if (type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None
            or type(size) is not int or not 1 <= size <= OFFICIAL_IMAGE_MAX_BYTES):
        fail('launcher_manifest_invalid')
    data = (OFFICIAL_LAUNCHER_TEMPLATE
            .replace(b'{image_sha256}', digest.encode('ascii'))
            .replace(b'{image_bytes}', str(size).encode('ascii')))
    if b'{' in data or any(len(line) >= 8191 for line in data.split(b'\r\n')):
        fail('launcher_invalid')
    return data


def _official_control(control_dir, image_manifest):
    """CONTROL must be exactly the generated launcher; anything else is refused."""
    try:
        plain(control_dir, directory=True)
        entries = sorted(os.listdir(control_dir))
    except OSError:
        fail('control_invalid')
    if entries != sorted(OFFICIAL_CONTROL_INVENTORY):
        fail('control_invalid')
    data = file_bytes(control_dir/OFFICIAL_LAUNCHER_NAME)
    if not data or data != official_launcher(image_manifest):
        fail('control_mismatch')
    return data


def _official_payload_ready(value):
    """The launcher needs manifest-inventoried payload layout members."""
    names = {entry['path'] for entry in value['files']}
    required = {'python/python.exe',
                'source/tests/test_research_claude_profile_native.py'}
    if not required <= names:
        fail('payload_layout_unsupported')
    for prefix in ('source/', 'source/src/', 'python/Lib/site-packages/'):
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


def official_control(image_dir, destination):
    """Validate IMAGE, exclusively create CONTROL, write the launcher; no launch."""
    image_dir = _official_path_argument(image_dir)
    destination = _official_path_argument(destination)
    _plain_ancestry(image_dir)
    value = _official_image(image_dir)
    _plain_ancestry(destination)
    if os.path.lexists(destination):
        fail('destination_exists')
    _reject_mapping_overlap(image_dir, destination)
    launcher = official_launcher(value)
    try:
        destination.mkdir()
    except FileExistsError:
        fail('destination_exists')
    plain(destination, directory=True)
    _reject_mapping_overlap(image_dir, destination)
    _exclusive_write(destination/OFFICIAL_LAUNCHER_NAME, launcher)
    return dict(status='official_control_generated_not_launched',
                image_sha256=value['sha256'], image_bytes=value['bytes'],
                image_version=value['version'], official_cli_executed=False,
                activation_authorized=False)


def official_config(payload_root, image_dir, control_dir, output_dir, destination,
                    *, isolated_host_attested=False):
    """Coordinate validations, then exclusively create OUTPUT and the .wsb."""
    if isolated_host_attested is not True:
        fail('isolated_host_attestation_required')
    payload_root = _official_path_argument(payload_root)
    image_dir = _official_path_argument(image_dir)
    control_dir = _official_path_argument(control_dir)
    output_dir = _official_path_argument(output_dir)
    destination = _official_path_argument(destination, file=True)
    _plain_ancestry(payload_root)
    _official_payload_ready(verify(payload_root))
    _plain_ancestry(image_dir)
    value = _official_image(image_dir)
    launcher = official_launcher(value)
    _plain_ancestry(control_dir)
    _official_control(control_dir, value)
    _plain_ancestry(output_dir)
    if os.path.lexists(output_dir):
        fail('output_dir_exists')
    _plain_ancestry(destination)
    if os.path.lexists(destination):
        fail('destination_exists')
    _reject_mapping_overlap(payload_root, image_dir, control_dir, output_dir,
                            destination)
    try:
        output_dir.mkdir()
    except FileExistsError:
        fail('output_dir_exists')
    plain(output_dir, directory=True)
    _reject_mapping_overlap(payload_root, image_dir, control_dir, output_dir)
    _reject_mapping_overlap(output_dir, destination)
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
    p = sub.add_parser('official-control', allow_abbrev=False)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p = sub.add_parser('official-config', allow_abbrev=False)
    p.add_argument('--payload-root', type=Path, required=True)
    p.add_argument('--image-dir', type=Path, required=True)
    p.add_argument('--control-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--isolated-host-attested', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'build': result = build(args.source, args.output, args.allow_ci_build)
        elif args.command == 'stage': result = stage(args.archive, args.sha256, args.destination)
        elif args.command == 'selftest': result = selftest(args.root, args.receipt)
        elif args.command == 'official-control':
            result = official_control(args.image_dir, args.destination)
        elif args.command == 'official-config':
            result = official_config(args.payload_root, args.image_dir, args.control_dir,
                                     args.output_dir, args.destination,
                                     isolated_host_attested=args.isolated_host_attested)
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
