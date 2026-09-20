"""Offline TEST-environment packaging/preparation; never a vendor CLI launcher.

Build only on a disposable Windows CI host. Stage/verify use stdlib and never
modify global tools, OS features, firewall or project business installations.
The generated Sandbox has no network/clipboard and maps only fresh input/output
folders. A smoke check is not official-image acceptance or an isolation proof.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.metadata as metadata
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
    selected = git('ls-files', '--stage', '-z', 'src', *SOURCE_EXTRA).decode().split('\0')
    from hashlib import sha1
    for entry in filter(None, selected):
        fields, name = entry.split('\t', 1)
        mode, expected, index = fields.split()
        if mode != '100644' or index != '0': fail('source_mode_invalid')
        data = file_bytes(source/name)
        if sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != expected:
            fail('source_changed')
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
    args = parser.parse_args()
    try:
        if args.command == 'build': result = build(args.source, args.output, args.allow_ci_build)
        elif args.command == 'stage': result = stage(args.archive, args.sha256, args.destination)
        elif args.command == 'selftest': result = selftest(args.root, args.receipt)
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
