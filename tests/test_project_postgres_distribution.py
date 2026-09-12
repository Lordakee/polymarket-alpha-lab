"""Clean source distribution tests. Fixtures contain no live engine or DB."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

from polymarket_alpha_lab.project_postgres import distribution as mod
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / 'Source Project'
    root.mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'user.name', 'Synthetic Fixture')
    git(root, 'config', 'user.email', 'synthetic@example.invalid')
    git(root, 'config', 'core.autocrlf', 'false')
    for name in mod.FIXED:
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('synthetic fixture\n', encoding='utf-8')
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n', encoding='utf-8')
    (root / 'database/migrations.lock.json').write_text('{}', encoding='utf-8')
    for name in ('src/polymarket_alpha_lab/__init__.py', 'src/polymarket_alpha_lab/module.py',
                 'supabase/migrations/20200101000000_fixture.sql', '.env',
                 '.local/postgres/app.pgpass', 'tests/private_fixture.py'):
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('synthetic private excluded\n' if not mod.selected_source(name) else '# synthetic code\n', encoding='utf-8')
    git(root, 'add', '-A')
    git(root, 'commit', '-qm', 'synthetic baseline')
    return root


@pytest.fixture
def native(tmp_path, monkeypatch):
    prefix = tmp_path / 'Explicit Trusted Prefix'
    for name in ('bin/postgres.exe', 'lib/native.dll', 'share/postgres.bki', 'COPYRIGHT',
                 'doc/postgresql/html/legalnotice.html', 'data/PG_VERSION', 'data/credentials', 'pgAdmin/private.txt'):
        path = prefix / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'Synthetic native fixture, not executable.\n')
    monkeypatch.setattr(mod, 'runtime_version', lambda _: '17.11')
    monkeypatch.setattr(mod, 'require_windows', lambda: None)
    return prefix


def extract_owned(archive, destination):
    # Only archives created by the fixture under test, not untrusted user input.
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            mod.safe_name(item.filename)
            target = destination / item.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(item))
    return destination / mod.TOP


def kit(checkout, native, tmp_path):
    archive = tmp_path / 'kit.zip'
    receipt = mod.build_distribution(checkout, native, archive)
    installed = extract_owned(archive, tmp_path / 'Installed')
    return archive, installed, receipt


def test_build_verified_relocatable_clean_kit(checkout, native, tmp_path):
    # Tracked private files and untracked code never enter the artifact.
    (checkout / 'src/polymarket_alpha_lab/untracked.py').write_text('sensitive fixture')
    archive, installed, receipt = kit(checkout, native, tmp_path)
    manifest = mod.verify_distribution(installed)
    assert receipt['archive_sha256'] == sha256(archive.read_bytes()).hexdigest()
    assert receipt['source_commit'] == git(checkout, 'rev-parse', 'HEAD').decode().strip()
    assert receipt['source_tree'] == git(checkout, 'rev-parse', 'HEAD^{tree}').decode().strip()
    assert receipt['database_included'] is receipt['python_included'] is False
    assert not (installed / '.env').exists()
    assert not (installed / '.local').exists()
    assert not (installed / '.git').exists()
    assert not (installed / 'tests').exists()
    assert not (installed / 'src/polymarket_alpha_lab/untracked.py').exists()
    with zipfile.ZipFile(installed / mod.ENGINE) as seed:
        assert 'pgsql/COPYRIGHT' in seed.namelist()
        assert 'pgsql/doc/postgresql/html/legalnotice.html' in seed.namelist()
        assert all(not n.startswith(('pgsql/data/', 'pgsql/pgAdmin/')) for n in seed.namelist())
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist()) == receipt['file_count'] + 1
    assert manifest['files'][mod.ENGINE] == sha256((installed / mod.ENGINE).read_bytes()).hexdigest()
    assert not (archive.with_name('kit.zip.building')).exists()


def test_identical_inputs_build_identical_zip(checkout, native, tmp_path):
    one, two = tmp_path / 'one.zip', tmp_path / 'two.zip'
    mod.build_distribution(checkout, native, one)
    mod.build_distribution(checkout, native, two)
    assert one.read_bytes() == two.read_bytes()


def test_dirty_tracked_source_fails_before_engine_probe(checkout, native, tmp_path, monkeypatch):
    (checkout / 'src/polymarket_alpha_lab/module.py').write_text('changed')
    monkeypatch.setattr(mod, 'runtime_version', lambda _: pytest.fail('probe before source check'))
    with pytest.raises(ProjectDatabaseError, match='dirty_source'):
        mod.build_distribution(checkout, native, tmp_path / 'kit.zip')
    assert not (tmp_path / 'kit.zip').exists()


def test_excluded_untracked_state_never_read(checkout, native, tmp_path):
    (checkout / '.local/postgres/extra.pgpass').write_text('must not be shipped')
    archive, installed, _ = kit(checkout, native, tmp_path)
    assert not (installed / '.local').exists()
    mod.verify_distribution(installed)


@pytest.mark.parametrize('name', ('../a.py', '/a.py', 'a//b.py', './a.py', 'a/../b',
    'a\\b.py', 'C:/secret', 'a/CON', 'a/NUL.txt', 'a/AUX.exe', 'a/file.', 'a/file ',
    'a/file\n', 'a/file\0', 'a/x:stream', 'a/<x>', '', 'a/' ))
def test_nonportable_paths_rejected(name):
    with pytest.raises(ProjectDatabaseError): mod.safe_name(name)


@pytest.mark.parametrize('name', ('.env', '.local/postgres/app.pgpass', 'runtime/postgres/data/PG_VERSION',
    '.git/config', 'tests/fixture.py', 'src/polymarket_alpha_lab/.env', 'docs/private.md',
    'src/polymarket_alpha_lab/__pycache__/x.py', 'supabase/migrations/nested/x.sql'))
def test_source_selection_excludes_private_and_unneeded_paths(name):
    assert not mod.selected_source(name)


@pytest.mark.parametrize('name', ('src/polymarket_alpha_lab/module.py', mod.ENGINE,
                                  'supabase/migrations/20200101000000_fixture.sql'))
def test_changed_payload_rejected(checkout, native, tmp_path, name):
    _, installed, _ = kit(checkout, native, tmp_path)
    target = installed / name
    target.write_bytes(target.read_bytes() + b'changed')
    with pytest.raises(ProjectDatabaseError, match='changed'): mod.verify_distribution(installed)


@pytest.mark.parametrize('name', ('src/polymarket_alpha_lab/injected.py',
                                  'supabase/migrations/20990101000000_new.sql'))
def test_unlisted_executable_code_or_migration_rejected(checkout, native, tmp_path, name):
    _, installed, _ = kit(checkout, native, tmp_path)
    (installed / name).write_bytes(b'# new')
    with pytest.raises(ProjectDatabaseError, match='changed'): mod.verify_distribution(installed)


@pytest.mark.parametrize('change', ('missing', 'extra', 'hash', 'target', 'version', 'source', 'paths'))
def test_malformed_manifest_rejected(checkout, native, tmp_path, change):
    _, installed, _ = kit(checkout, native, tmp_path)
    path = installed / mod.MANIFEST
    value = json.loads(path.read_bytes())
    if change == 'missing': del value['files'][mod.ENGINE]
    elif change == 'extra': value['unexpected'] = True
    elif change == 'hash': value['files'][mod.ENGINE] = 'bad'
    elif change == 'target': value['target'] = 'anything'
    elif change == 'version': value['postgres_version'] = '18.1'
    elif change == 'source': value['source_commit'] = 'not-a-commit'
    elif change == 'paths': value['files']['../private'] = '0' * 64
    path.write_text(json.dumps(value), encoding='utf-8')
    with pytest.raises(ProjectDatabaseError): mod.verify_distribution(installed)


def test_duplicate_json_keys_rejected(checkout, native, tmp_path):
    _, installed, _ = kit(checkout, native, tmp_path)
    path = installed / mod.MANIFEST
    path.write_text('{"format":"a","format":"b"}', encoding='utf-8')
    with pytest.raises(ProjectDatabaseError): mod.verify_distribution(installed)


def test_runtime_replaced_during_pack_fails_without_final(checkout, native, tmp_path, monkeypatch):
    original = mod.inventory
    def stale(prefix):
        result = original(prefix)
        (prefix / 'bin/postgres.exe').write_bytes(b'changed after hash')
        return result
    monkeypatch.setattr(mod, 'inventory', stale)
    with pytest.raises(ProjectDatabaseError, match='runtime_changed'):
        mod.build_distribution(checkout, native, tmp_path / 'kit.zip')
    assert not (tmp_path / 'kit.zip').exists()


def test_unlicensed_prefix_is_not_distributed(checkout, native, tmp_path):
    (native / 'COPYRIGHT').unlink()
    (native / 'doc/postgresql/html/legalnotice.html').unlink()
    with pytest.raises(ProjectDatabaseError, match='notice_required'):
        mod.build_distribution(checkout, native, tmp_path / 'kit.zip')


def test_fonts_are_not_shipped(checkout, native, tmp_path):
    (native / 'share/private.ttf').write_bytes(b'font fixture')
    with pytest.raises(ProjectDatabaseError, match='runtime_path'):
        mod.build_distribution(checkout, native, tmp_path / 'kit.zip')


def test_existing_output_never_overwritten(checkout, native, tmp_path):
    output = tmp_path / 'kit.zip'
    output.write_bytes(b'original')
    with pytest.raises(ProjectDatabaseError): mod.build_distribution(checkout, native, output)
    assert output.read_bytes() == b'original'


def test_partial_output_never_overwritten(checkout, native, tmp_path):
    output = tmp_path / 'kit.zip'
    partial = tmp_path / 'kit.zip.building'
    partial.write_bytes(b'original partial')
    with pytest.raises(FileExistsError): mod.build_distribution(checkout, native, output)
    assert partial.read_bytes() == b'original partial'
    assert not output.exists()


def test_publish_collision_does_not_replace_existing(checkout, native, tmp_path, monkeypatch):
    output = tmp_path / 'kit.zip'
    original = os.link
    def collision(source, target):
        Path(target).write_bytes(b'other build')
        original(source, target)
    monkeypatch.setattr(mod.os, 'link', collision)
    with pytest.raises(FileExistsError): mod.build_distribution(checkout, native, output)
    assert output.read_bytes() == b'other build'


def test_generated_local_state_is_not_part_of_manifest(checkout, native, tmp_path):
    _, installed, _ = kit(checkout, native, tmp_path)
    for name in ('.local/postgres/app.pgpass', '.venv/fixture.txt',
                 'src/polymarket_alpha_lab/__pycache__/module.pyc'):
        target = installed / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'local infrastructure')
    mod.verify_distribution(installed)


def test_export_ignore_cannot_silently_drop_code(checkout):
    (checkout / '.gitattributes').write_text('src/polymarket_alpha_lab/module.py export-ignore\n')
    git(checkout, 'add', '.gitattributes'); git(checkout, 'commit', '-qm', 'attribute fixture')
    with pytest.raises(ProjectDatabaseError, match='source_changed'): mod.committed_sources(checkout)
