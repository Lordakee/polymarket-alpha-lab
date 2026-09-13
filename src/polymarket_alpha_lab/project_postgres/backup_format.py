"""Closed, bounded physical-backup format. Never SQL, pickle or executable import.

Backups contain private database records AND generated credentials. A checksum
binds bytes; it is not encryption, publisher authentication or source approval.
"""
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import struct
import zipfile

from .files import digest_file, fail, no_links

FORMAT = 'project-postgres-cold-backup-v1'
MANIFEST = 'BACKUP.json'
MAX_ENTRIES = 50000
MAX_BYTES = 8 * 1024**3
MAX_MANIFEST_BYTES = 16 * 1024**2
CHUNK = 1024 * 1024
REQUIRED_FILES = {'instance.json', 'initialized', 'owner.pgpass', 'app.pgpass',
                  'data/PG_VERSION', 'data/global/pg_control', 'data/postgresql.conf',
                  'data/pg_hba.conf', 'data/postgresql.auto.conf'}
REQUIRED_DIRS = {'data', 'data/base', 'data/global', 'data/pg_wal', 'data/pg_xact', 'data/pg_tblspc'}
TOP_FILES = {'instance.json', 'initialized', 'owner.pgpass', 'app.pgpass', 'server.log'}
FORBIDDEN = {'data/postmaster.pid', 'data/backup_label', 'data/tablespace_map',
             'data/recovery.signal', 'data/standby.signal'}


def invalid():
    fail('project_postgres_backup_invalid')


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(',', ':')).encode('ascii')


def fingerprint(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def platform_id() -> str:
    return f'{platform.system().lower()}-{platform.machine().lower()}-{struct.calcsize("P") * 8}'


def valid_hash(value: object) -> bool:
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def safe_name(name: object) -> str:
    if (type(name) is not str or len(name) > 400 or not name
            or PurePosixPath(name).as_posix() != name or name.startswith('/')):
        invalid()
    for part in name.split('/'):
        if (part in ('.', '..') or part.endswith('.')
                or re.fullmatch(r'[A-Za-z0-9_.-]+', part) is None
                or re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', part, re.I)):
            invalid()
    if (name not in TOP_FILES and name != 'data' and not name.startswith('data/')):
        invalid()
    if name in FORBIDDEN or name.startswith('data/pg_tblspc/'):
        invalid()
    return name


def validate_entries(entries: object) -> dict:
    if type(entries) is not dict or not 1 <= len(entries) <= MAX_ENTRIES:
        invalid()
    seen, total = set(), 0
    for name, item in entries.items():
        safe_name(name)
        if name.casefold() in seen or type(item) is not dict:
            invalid()
        seen.add(name.casefold())
        if item == {'kind': 'directory'}:
            if name in TOP_FILES:
                invalid()
        elif (set(item) == {'kind', 'size', 'sha256'} and item['kind'] == 'file'
              and type(item['size']) is int and 0 <= item['size'] <= MAX_BYTES
              and valid_hash(item['sha256'])):
            total += item['size']
        else:
            invalid()
        if total > MAX_BYTES:
            invalid()
        for parent in PurePosixPath(name).parents:
            if str(parent) != '.' and entries.get(str(parent)) != {'kind': 'directory'}:
                invalid()
    if (any(entries.get(n, {}).get('kind') != 'file' for n in REQUIRED_FILES)
            or any(entries.get(n) != {'kind': 'directory'} for n in REQUIRED_DIRS)):
        invalid()
    return entries


def inventory(home: Path) -> dict:
    """Include empty directories, WAL, transaction state and credentials intact."""
    no_links(home)
    found, pending, total = {}, [home], 0
    while pending:
        parent = pending.pop()
        for path in sorted(parent.iterdir()):
            no_links(path)
            info = path.lstat()
            name = safe_name(path.relative_to(home).as_posix())
            if len(found) >= MAX_ENTRIES:
                invalid()
            if os.name != 'nt' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
                fail('project_postgres_private_permissions_required')
            if stat.S_ISDIR(info.st_mode):
                found[name] = {'kind': 'directory'}
                pending.append(path)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                total += info.st_size
                if total > MAX_BYTES:
                    invalid()
                found[name] = {'kind': 'file', 'size': info.st_size, 'sha256': digest_file(path)}
            else:
                invalid()
    return validate_entries(found)


def parse_manifest(raw: bytes) -> dict:
    if len(raw) > MAX_MANIFEST_BYTES:
        invalid()
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                invalid()
            result[key] = value
        return result
    try:
        data = json.loads(raw, object_pairs_hook=unique)
        if (type(data) is not dict or set(data) != {'format', 'created_at', 'platform', 'instance',
                'runtime_sha256', 'migrations_sha256', 'entries'} or data['format'] != FORMAT
                or type(data['platform']) is not str or not 1 <= len(data['platform']) <= 128
                or not valid_hash(data['runtime_sha256']) or not valid_hash(data['migrations_sha256'])):
            invalid()
        at = datetime.fromisoformat(data['created_at'])
        if at.tzinfo is None or at.utcoffset().total_seconds() != 0 or at.isoformat() != data['created_at']:
            invalid()
        info = data['instance']
        if (type(info) is not dict or set(info) != {'format', 'instance_id', 'root_sha256',
                'system_identifier', 'version', 'port'} or info['format'] != 'project-postgres-v1'
                or type(info['instance_id']) is not str or re.fullmatch('[0-9a-f]{32}', info['instance_id']) is None
                or not valid_hash(info['root_sha256']) or type(info['system_identifier']) is not str
                or re.fullmatch('[0-9]{1,20}', info['system_identifier']) is None
                or type(info['version']) is not str or re.fullmatch(r'(16|17|18)\.\d+', info['version']) is None
                or type(info['port']) is not int or not 1024 <= info['port'] <= 65535):
            invalid()
        validate_entries(data['entries'])
        if canonical(data) != raw:
            invalid()
        return data
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        invalid()


def inspect_archive(archive: zipfile.ZipFile) -> dict:
    """Fully stream/check all content BEFORE any restore destination is created."""
    members = archive.infolist()
    if len(members) > MAX_ENTRIES + 1 or len({x.filename for x in members}) != len(members):
        invalid()
    seen, total = {}, 0
    for item in members:
        if (item.orig_filename != item.filename or item.flag_bits & 1
                or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            invalid()
        name = item.filename.rstrip('/') if item.is_dir() else item.filename
        if item.filename != name + ('/' if item.is_dir() else ''):
            invalid()
        if name != MANIFEST:
            safe_name(name)
        elif item.is_dir() or item.file_size > MAX_MANIFEST_BYTES:
            invalid()
        if name in seen:
            invalid()
        seen[name] = item
        mode = stat.S_IFMT(item.external_attr >> 16)
        expected = stat.S_IFDIR if item.is_dir() else stat.S_IFREG
        if mode not in (0, expected) or item.file_size < 0 or (item.is_dir() and item.file_size != 0):
            invalid()
        total += item.file_size
        if total > MAX_BYTES + MAX_MANIFEST_BYTES:
            invalid()
    if MANIFEST not in seen:
        invalid()
    data = parse_manifest(archive.read(seen[MANIFEST]))
    if set(seen) != set(data['entries']) | {MANIFEST}:
        invalid()
    for name, expected in data['entries'].items():
        item = seen[name]
        if (expected['kind'] == 'directory') != item.is_dir():
            invalid()
        if item.is_dir():
            continue
        if item.file_size != expected['size']:
            invalid()
        digest, count = sha256(), 0
        with archive.open(item) as stream:
            for chunk in iter(lambda: stream.read(CHUNK), b''):
                count += len(chunk)
                if count > expected['size']:
                    invalid()
                digest.update(chunk)
        if count != expected['size'] or digest.hexdigest() != expected['sha256']:
            invalid()
    return data
