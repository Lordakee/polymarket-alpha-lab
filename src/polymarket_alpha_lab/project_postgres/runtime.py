"""Explicit native runtime import. No downloads, system services or PATH fallback.

Release packagers supply a trusted extracted PostgreSQL prefix or a ZIP plus
its independently approved SHA256. Hashes bind bytes, not publisher identity.
"""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile

from .files import Layout, clean_environment, command, digest_file, fail, no_links, private_directory, read_private, write_private

PROGRAMS = ('postgres', 'initdb', 'pg_ctl', 'psql', 'pg_controldata')
SUPPORTED_MAJORS = (16, 17, 18)
MAX_RUNTIME_BYTES = 1073741824



def native_spawn_settings(program: str, env: dict[str, str], *, windows: bool) -> dict:
    """Scope Windows descendants to native/system DLLs and a trusted cwd.

    initdb re-executes with a restricted token, and pg_ctl starts descendants.
    Both must resolve the same project runtime after the initial Python spawn.
    Never change the parent's cwd/PATH or disable native privilege dropping.
    """
    if not windows:
        return {'env': env}
    exe = Path(program)
    if exe.name not in tuple(name + '.exe' for name in PROGRAMS):
        fail('project_postgres_program_not_allowed')
    system = next((value for key, value in env.items() if key.upper() == 'SYSTEMROOT'), '')
    root = Path(system)
    if not exe.is_absolute() or exe.parent.name != 'bin' or not system or not root.is_absolute():
        fail('project_postgres_invalid_native_environment')
    child = {key: value for key, value in env.items() if key.upper() not in ('PATH', 'COMSPEC')}
    child['PATH'] = ';'.join(map(str, (exe.parent, exe.parent.parent / 'lib', root / 'System32', root)))
    child['COMSPEC'] = str(root / 'System32/cmd.exe')
    return {'env': child, 'cwd': str(exe.parent)}


def native_command(args: list[str], *, env=None, **options):
    environment = clean_environment() if env is None else env
    return command(args, **native_spawn_settings(args[0], environment, windows=os.name == 'nt'), **options)


def executable(prefix: Path, name: str) -> Path:
    if name not in PROGRAMS:
        fail('project_postgres_program_not_allowed')
    value = prefix / 'bin' / (name + ('.exe' if os.name == 'nt' else ''))
    no_links(value)
    if not value.is_file():
        fail('project_postgres_runtime_missing')
    return value


def runtime_version(prefix: Path) -> str:
    versions = []
    for name in PROGRAMS:
        value = native_command([str(executable(prefix, name)), '--version'], timeout=10).stdout.strip()
        match = re.fullmatch(r'\S+ \(PostgreSQL\) (\d+\.\d+)(?: \([^\r\n]*\))?', value)
        if not match or int(match[1].split('.')[0]) not in SUPPORTED_MAJORS:
            fail('project_postgres_unsupported_runtime')
        versions.append(match[1])
    if len(set(versions)) != 1 or not (prefix / 'share/postgres.bki').is_file():
        fail('project_postgres_inconsistent_runtime')
    return versions[0]


def inventory(prefix: Path) -> dict[str, str]:
    found, total = {}, 0
    for base in ('bin', 'lib', 'share'):
        if not (prefix / base).is_dir():
            fail('project_postgres_runtime_missing')
        for item in sorted((prefix / base).rglob('*')):
            no_links(item)
            if item.is_file():
                total += item.stat().st_size
                if total > MAX_RUNTIME_BYTES or len(found) >= 20000:
                    fail('project_postgres_runtime_too_large')
                found[item.relative_to(prefix).as_posix()] = digest_file(item)
    return found


def verify_runtime(layout: Layout) -> dict:
    try:
        private_directory(layout.runtime)
        record = json.loads(read_private(layout.runtime / 'runtime.json', limit=4000000))
        if (set(record) != {'format', 'version', 'files'} or record['format'] != 'native-postgres-v1'
                or record['files'] != inventory(layout.runtime)):
            fail('project_postgres_runtime_changed')
        if record['version'] != runtime_version(layout.runtime):
            fail('project_postgres_runtime_changed')
        return record
    except (OSError, ValueError, TypeError):
        fail('project_postgres_runtime_invalid')


def _finish_import(layout: Layout, target: Path) -> str:
    # Version probes execute ONLY after explicit directory trust or archive hash
    # verification. No command from a model/provider payload reaches this path.
    version = runtime_version(target)
    write_private(target / 'runtime.json', json.dumps({
        'format': 'native-postgres-v1', 'version': version, 'files': inventory(target)}, sort_keys=True))
    target.rename(layout.runtime)
    return version


def _staging(layout: Layout) -> Path:
    parent = layout.runtime.parent
    no_links(parent)
    if not parent.exists():
        private_directory(parent, create=True)
    else:
        private_directory(parent)
    if layout.runtime.exists():
        fail('project_postgres_runtime_already_installed')
    target = parent / 'postgres.installing'
    if target.exists():
        fail('project_postgres_incomplete_runtime_install')
    private_directory(target, create=True)
    return target


def import_runtime_directory(root: Path, source: Path) -> str:
    """Copy an explicitly trusted portable prefix; never adopt its databases."""
    layout = Layout(root)
    source = Path(source).absolute()
    no_links(source)
    if source == layout.runtime or source.is_relative_to(layout.private):
        fail('project_postgres_invalid_runtime_source')
    # Validate the entire source before creating any target files.
    inventory(source)
    with layout.lock():
        target = _staging(layout)
        for name in ('bin', 'lib', 'share'):
            shutil.copytree(source / name, target / name, symlinks=False)
        for name in ('COPYRIGHT', 'LICENSE', 'LICENSE.txt', 'THIRDPARTYLICENSE.txt'):
            if (source / name).is_file():
                no_links(source / name)
                shutil.copyfile(source / name, target / name)
        return _finish_import(layout, target)


def zip_members(archive: zipfile.ZipFile) -> tuple[tuple[zipfile.ZipInfo, PurePosixPath], ...]:
    selected, seen, total = [], set(), 0
    if len(archive.infolist()) > 50000:
        fail('project_postgres_invalid_runtime_archive')
    for item in archive.infolist():
        # ZipInfo retains the wire name separately before NUL truncation and
        # Windows separator normalization. Reject, never trust the rewritten name.
        if item.orig_filename != item.filename:
            fail('project_postgres_invalid_runtime_archive')
        path = PurePosixPath(item.filename)
        if ('\\' in item.filename or path.is_absolute() or '..' in path.parts
                or any(':' in p or p.endswith((' ', '.')) for p in path.parts)
                or stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR)
                or any(re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', p, re.I)
                       or any(ord(c) < 32 for c in p) for p in path.parts)
                or item.flag_bits & 1):
            fail('project_postgres_invalid_runtime_archive')
        if not path.parts or path.parts[0] != 'pgsql':
            fail('project_postgres_invalid_runtime_archive')
        relative = PurePosixPath(*path.parts[1:])
        if not relative.parts or item.is_dir():
            continue
        # No pgAdmin, StackBuilder, user data, executables chosen by the archive,
        # or database journals. Retain the PostgreSQL runtime and its notices.
        if relative.parts[0] not in ('bin', 'lib', 'share') and relative.name not in (
                'COPYRIGHT', 'LICENSE', 'LICENSE.txt', 'THIRDPARTYLICENSE.txt'):
            continue
        key = str(relative).casefold()
        total += item.file_size
        if key in seen or total > MAX_RUNTIME_BYTES or len(selected) >= 20000:
            fail('project_postgres_invalid_runtime_archive')
        seen.add(key)
        selected.append((item, relative))
    return tuple(selected)


def import_runtime_archive(root: Path, archive_path: Path, *, expected_sha256: str) -> str:
    """No executable is run until the complete archive matches the approved hash."""
    layout = Layout(root)
    path = Path(archive_path).absolute()
    no_links(path)
    if (type(expected_sha256) is not str or not re.fullmatch(r'[0-9a-f]{64}', expected_sha256)
            or path.stat().st_size > MAX_RUNTIME_BYTES or digest_file(path) != expected_sha256):
        fail('project_postgres_runtime_checksum_mismatch')
    with layout.lock(), zipfile.ZipFile(path) as archive:
        selected = zip_members(archive)
        target = _staging(layout)
        for item, relative in selected:
            dest = target.joinpath(*relative.parts)
            # The staging root already has an explicit current-user/SYSTEM ACL.
            # On Windows, mkdir(0700) installs an OWNER RIGHTS/admin ACL instead
            # of inheriting it. An elevated owner can then be Administrators,
            # which PostgreSQL deliberately removes from its child token.
            # Non-0700 mode is ignored by Windows: inherit our private ACL.
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o777 if os.name == 'nt' else 0o700)
            with archive.open(item) as source, dest.open('xb') as output:
                shutil.copyfileobj(source, output)
            if os.name != 'nt':
                dest.chmod(0o700 if relative.parts[0] == 'bin' else 0o600)
        return _finish_import(layout, target)
