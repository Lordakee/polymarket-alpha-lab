"""Build a clean Windows source + native engine kit, never a database backup.

Source bytes come from a committed Git tree. Only explicitly selected code and
migration paths are shipped. The engine is an explicitly trusted native prefix;
no downloads, installed clusters, credentials or arbitrary workspace files.
Checksums detect changed bytes, not publisher identity or malicious source code.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import zipfile

from .files import Layout, clean_environment, digest_file, fail, no_links
from .runtime import MAX_RUNTIME_BYTES, inventory, runtime_version

FORMAT = 'project-native-distribution-v1'
MANIFEST = 'PROJECT-BUNDLE.json'
ENGINE = 'database/postgres-runtime.zip'
TOP = 'polymarket-alpha-lab'
FIXED = ('pyproject.toml', 'uv.lock', '.gitignore', '.gitattributes', 'database/README.md',
         'database/quickstart.md', 'database/migrations.lock.json',
         'scripts/project_database.py', 'scripts/start_project.py')
# Optional reviewed entrypoints: old kits without them remain verifiable.
PUBLIC_ENTRYPOINTS = ('docs/research-local-agent.md', 'docs/research-paper-settlement.md', 'docs/research-paper.md', 'scripts/manage_research_tasks.py', 'docs/research-model-budget.md', 'docs/research-dispatch.md', 'scripts/inspect_project_resolution.py', 'docs/research-resolution-inspection.md',
    'scripts/list_project_research.py', 'docs/research-execution-inventory.md',
    'scripts/inspect_project_research.py', 'docs/research-execution-inspection.md',
    'scripts/evaluate_project_research.py', 'docs/research-evaluation-console.md',
    'scripts/review_resolution_queue.py', 'scripts/preview_crypto_research.py',
    'scripts/discover_crypto_research.py', 'scripts/download_handoff.ps1',
    'docs/research-resolution-queue.md', 'docs/research-crypto-launch.md', 'docs/research-crypto-discovery.md',
    'docs/research-crypto-contract-scope.md', 'docs/research-crypto-observation-time.md')
SOURCE_ROOTS = ('src/polymarket_alpha_lab', 'supabase/migrations')
MAX_SOURCE_BYTES = 134217728
MAX_FILES = 20000
NOTICE_NAMES = ('COPYRIGHT', 'LICENSE', 'LICENSE.txt', 'THIRDPARTYLICENSE.txt')
FONT_SUFFIXES = ('.ttf', '.otf', '.woff', '.woff2', '.eot', '.ttc')


def safe_name(name: str) -> str:
    if (type(name) is not str or not name or len(name) > 400
            or PurePosixPath(name).as_posix() != name
            or PurePosixPath(name).is_absolute() or '\\' in name):
        fail('project_bundle_invalid_path')
    for part in name.split('/'):
        if (part in ('', '.', '..') or part.endswith((' ', '.'))
                or any(ord(c) < 32 or c in ':<>"|?*' for c in part)
                or re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', part, re.I)):
            fail('project_bundle_invalid_path')
    return name


def selected_source(name: str) -> bool:
    if name in FIXED or name in PUBLIC_ENTRYPOINTS:
        return True
    if name.startswith('src/polymarket_alpha_lab/') and name.endswith('.py'):
        return not any(part.startswith('.') or part == '__pycache__' for part in name.split('/'))
    return name.startswith('supabase/migrations/') and '/' not in name[len('supabase/migrations/'):] and name.endswith('.sql')


def _git(root: Path, *args: str) -> bytes:
    # Build-time Git only, never an application dependency. Disable inherited
    # alternate repositories/global configuration and optional fsmonitor hooks.
    executable = shutil.which('git')
    if not executable:
        fail('project_bundle_git_required')
    env = {k: v for k, v in clean_environment().items() if not k.upper().startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0')
    try:
        result = subprocess.run([executable, '--literal-pathspecs', '-C', str(root),
            '-c', 'core.fsmonitor=false', *args], env=env, stdin=subprocess.DEVNULL,
            capture_output=True, timeout=90, check=False, shell=False)
    except (OSError, subprocess.SubprocessError):
        fail('project_bundle_source_failed')
    if result.returncode:
        fail('project_bundle_source_failed')
    return result.stdout


def committed_sources(root: Path) -> tuple[dict[str, bytes], str, str]:
    """Use only HEAD blobs, reject dirty tracked source, ignore untracked files."""
    commit = _git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    tree = _git(root, 'rev-parse', '--verify', 'HEAD^{tree}').decode().strip()
    if not all(re.fullmatch('[0-9a-f]{40}', value) for value in (commit, tree)):
        fail('project_bundle_source_failed')
    staged = _git(root, 'diff', '--cached', '--name-only', '-z', 'HEAD').decode('utf-8').split('\0')
    if any(selected_source(name) for name in staged):
        fail('project_bundle_dirty_source')
    indexed, total = {}, 0
    for entry in _git(root, 'ls-tree', '-rlz', '--full-tree', 'HEAD').split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        name = raw_name.decode('utf-8')
        if not selected_source(name):
            continue
        safe_name(name)
        mode, kind, blob, size = metadata.split()
        if mode not in (b'100644', b'100755') or kind != b'blob':
            fail('project_bundle_nonregular_source')
        total += int(size)
        if total > MAX_SOURCE_BYTES or len(indexed) >= MAX_FILES:
            fail('project_bundle_source_limit')
        indexed[name] = blob.decode()
    if not set(FIXED).issubset(indexed) or not any(n.startswith('src/') for n in indexed):
        fail('project_bundle_required_source_missing')
    if len({name.casefold() for name in indexed}) != len(indexed):
        fail('project_bundle_path_collision')
    archive = _git(root, 'archive', '--format=tar', 'HEAD', '--', *FIXED, *SOURCE_ROOTS,
                   *(name for name in PUBLIC_ENTRYPOINTS if name in indexed))
    if len(archive) > MAX_SOURCE_BYTES + MAX_FILES * 2048:
        fail('project_bundle_source_limit')
    sources = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for item in tar:
            if item.name not in indexed:
                continue
            if not item.isfile() or item.name in sources:
                fail('project_bundle_nonregular_source')
            stream = tar.extractfile(item)
            raw = stream.read()
            blob = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if blob != indexed[item.name]:
                fail('project_bundle_source_changed')
            target = root / item.name
            no_links(target)
            if not target.is_file():
                fail('project_bundle_dirty_source')
            with target.open('rb') as worktree:
                observed = worktree.read(len(raw) * 2 + 1)
            # HEAD remains the exact artifact source. Accept ordinary LF->CRLF
            # text checkout conversion without trusting global Git filters; do
            # not accept content edits, staged additions or linked source files.
            if observed != raw and observed.replace(b'\r\n', b'\n') != raw:
                fail('project_bundle_dirty_source')
            sources[item.name] = raw
    if sources.keys() != indexed.keys() or _git(root, 'rev-parse', 'HEAD').decode().strip() != commit:
        fail('project_bundle_source_changed')
    return sources, commit, tree


def _entry(name: str) -> zipfile.ZipInfo:
    item = zipfile.ZipInfo(safe_name(name), (1980, 1, 1, 0, 0, 0))
    item.create_system = 3
    item.external_attr = (stat.S_IFREG | 0o600) << 16
    return item


def _native_seed(prefix: Path, output) -> str:
    """Caller has explicitly trusted the prefix before its version probes run."""
    version = runtime_version(prefix)
    if version.split('.')[0] != '17':
        fail('project_bundle_requires_postgres_17')
    expected = inventory(prefix)
    # Preserve supplied root notices AND relevant notices under the documentation
    # directory, without shipping pgAdmin, examples, fonts or other applications.
    for name in NOTICE_NAMES:
        path = prefix / name
        if path.exists():
            no_links(path)
            expected[name] = digest_file(path)
    doc = prefix / 'doc'
    if doc.exists():
        no_links(doc)
        for item in doc.rglob('*'):
            no_links(item)
            if item.is_file() and re.search(r'copyright|licen[cs]e|legalnotice', item.name, re.I):
                expected[item.relative_to(prefix).as_posix()] = digest_file(item)
    if not any(re.search(r'copyright|licen[cs]e|legalnotice', n, re.I) for n in expected):
        fail('project_bundle_runtime_notice_required')
    seen, total = set(), 0
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, expected_hash in sorted(expected.items()):
            safe_name(name)
            if name.casefold() in seen or name.lower().endswith(FONT_SUFFIXES):
                fail('project_bundle_runtime_path_rejected')
            seen.add(name.casefold())
            path = prefix / name
            no_links(path)
            info = path.stat()
            if not stat.S_ISREG(info.st_mode):
                fail('project_bundle_runtime_path_rejected')
            total += info.st_size
            if total > MAX_RUNTIME_BYTES or len(seen) > MAX_FILES:
                fail('project_bundle_runtime_limit')
            item = _entry('pgsql/' + name)
            item.compress_type = zipfile.ZIP_DEFLATED
            actual = sha256()
            with path.open('rb') as source, archive.open(item, 'w', force_zip64=True) as dest:
                while chunk := source.read(1048576):
                    actual.update(chunk)
                    dest.write(chunk)
            if actual.hexdigest() != expected_hash:
                fail('project_bundle_runtime_changed')
    output.seek(0)
    return version


def require_windows() -> None:
    import platform
    if os.name != 'nt' or platform.machine().upper() not in ('AMD64', 'X86_64'):
        fail('project_bundle_windows_x64_required')


def build_distribution(root: Path, prefix: Path, destination: Path) -> dict:
    """Publish one new kit ZIP atomically; never overwrite a prior artifact.

    Windows/x64 PostgreSQL 17 is the sole delivered binary target. Python and
    the locked Python dependencies are NOT bundled. This is not an updater.
    """
    require_windows()
    layout = Layout(root)
    prefix, destination = Path(prefix).absolute(), Path(destination).absolute()
    no_links(prefix)
    no_links(destination)
    if not destination.parent.is_dir() or destination.exists() or destination.suffix.lower() != '.zip':
        fail('project_bundle_new_zip_required')
    # Writing into a live cluster/runtime would violate their integrity guards.
    if destination.is_relative_to(layout.private) or destination.is_relative_to(layout.runtime):
        fail('project_bundle_invalid_destination')
    sources, commit, tree = committed_sources(layout.root)
    partial = destination.with_name(destination.name + '.building')
    no_links(partial)
    with tempfile.TemporaryFile() as seed:
        version = _native_seed(prefix, seed)
        engine_hash = sha256()
        while chunk := seed.read(1048576):
            engine_hash.update(chunk)
        seed.seek(0)
        manifest = dict(format=FORMAT, source_commit=commit, source_tree=tree,
            target='windows-x86_64', postgres_version=version, python_requires='>=3.11',
            files={name: sha256(raw).hexdigest() for name, raw in sorted(sources.items())})
        manifest['files'][ENGINE] = engine_hash.hexdigest()
        # EXCL plus atomic hard-link publication: interrupted builds never expose
        # a final ZIP, and concurrent builds cannot overwrite each other's files.
        with partial.open('xb') as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for name, raw in sorted(sources.items()):
                    item = _entry(TOP + '/' + name)
                    item.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(item, raw)
                archive.writestr(_entry(TOP + '/' + MANIFEST), json.dumps(manifest, sort_keys=True).encode())
                with archive.open(_entry(TOP + '/' + ENGINE), 'w', force_zip64=True) as target:
                    shutil.copyfileobj(seed, target)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(partial, destination)
        partial.unlink()
    return dict(status='built', source_commit=commit, source_tree=tree, postgres_version=version,
        file_count=len(manifest['files']), archive_sha256=digest_file(destination),
        archive_bytes=destination.stat().st_size, database_included=False, python_included=False)


def verify_distribution(root: Path) -> dict:
    """Check a trusted extracted kit before native import/initialization.

    This is integrity checking, not a safe executor for untrusted downloaded
    Python code. Verify the OUTER ZIP hash through a trusted channel first.
    Generated .venv/.local/runtime are outside this immutable distribution set.
    """
    from polymarket_alpha_lab.team_research_agent_types import strict_json
    layout = Layout(root)
    path = layout.root / MANIFEST
    no_links(path)
    try:
        if not path.is_file() or path.stat().st_size > 4000000:
            raise ValueError
        manifest = strict_json(path.read_text(encoding='utf-8'))
        keys = {'format', 'source_commit', 'source_tree', 'target', 'postgres_version', 'python_requires', 'files'}
        if (type(manifest) is not dict or set(manifest) != keys or manifest['format'] != FORMAT
                or manifest['target'] != 'windows-x86_64' or manifest['python_requires'] != '>=3.11'
                or re.fullmatch(r'17\.\d+', manifest['postgres_version']) is None
                or any(re.fullmatch('[0-9a-f]{40}', manifest[k]) is None for k in ('source_commit', 'source_tree'))):
            raise ValueError
        values = manifest['files']
        if type(values) is not dict or not len(FIXED) + 2 <= len(values) <= MAX_FILES:
            raise ValueError
        if not set((*FIXED, ENGINE)).issubset(values):
            raise ValueError
        names, total = set(), 0
        for name, checksum in values.items():
            safe_name(name)
            if name != ENGINE and not selected_source(name):
                raise ValueError
            if type(checksum) is not str or re.fullmatch('[0-9a-f]{64}', checksum) is None:
                raise ValueError
            if name.casefold() in names:
                raise ValueError
            names.add(name.casefold())
            target = layout.root / name
            no_links(target)
            info = target.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_size > (MAX_RUNTIME_BYTES if name == ENGINE else MAX_SOURCE_BYTES):
                raise ValueError
            if name != ENGINE:
                total += info.st_size
            if total > MAX_SOURCE_BYTES or digest_file(target) != checksum:
                raise ValueError
        # Do not let an extra Python module or unlisted migration change startup.
        actual = set(FIXED)
        for name in PUBLIC_ENTRYPOINTS:
            target = layout.root / name
            no_links(target)
            if target.exists():
                actual.add(name)
        for name in SOURCE_ROOTS:
            for target in (layout.root / name).rglob('*'):
                no_links(target)
                relative = target.relative_to(layout.root).as_posix()
                if target.is_file() and selected_source(relative):
                    actual.add(relative)
        if actual | {ENGINE} != set(values):
            raise ValueError
        return manifest
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        fail('project_bundle_invalid_or_changed')
