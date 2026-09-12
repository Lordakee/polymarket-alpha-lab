"""First startup refuses to replace existing or partial project infrastructure."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.project_postgres import bootstrap as mod
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / 'Project'
    (root / 'database').mkdir(parents=True)
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root / 'database/migrations.lock.json').write_text('{}')
    events = []
    monkeypatch.setattr(mod, 'require_windows', lambda: None)
    monkeypatch.setattr(mod.importlib.util, 'find_spec', lambda _: object())
    monkeypatch.setattr(mod, 'verify_runtime', lambda _: dict(version='17.11'))
    monkeypatch.setattr(mod, 'verify_distribution', lambda _: dict(
        files={mod.ENGINE: 'f' * 64}, postgres_version='17.11', source_commit='a' * 40))
    def imported(root, seed, *, expected_sha256):
        events.append(('import', expected_sha256))
        (root / 'runtime/postgres').mkdir(parents=True)
    monkeypatch.setattr(mod, 'import_runtime_archive', imported)
    class Session:
        def __enter__(self):
            events.append('session_enter'); return self
        def __exit__(self, *args): events.append('session_exit')
        def evaluate(self):
            events.append('evaluate')
            return SimpleNamespace(records=(), outcomes=())
    class DB:
        def __init__(self, root): self.root = root
        def initialize(self, *, port):
            events.append(('init', port))
            (root / '.local/postgres').mkdir(parents=True)
        def status(self):
            events.append('status')
            return dict(port=55432, instance_id='id')
        def session(self): return Session()
    monkeypatch.setattr(mod, 'ProjectPostgres', DB)
    return root, events, DB


def seed(root):
    (root / mod.ENGINE).write_bytes(b'synthetic archive')
    (root / mod.MANIFEST).write_text('{}')


def test_first_start_and_repeat_have_no_reset_or_reimport(setup):
    root, events, _ = setup; seed(root)
    first = mod.prepare_project(root)
    second = mod.prepare_project(root)
    assert first['initialized_here'] is True
    assert second['initialized_here'] is False
    assert events.count(('init', 55432)) == 1
    assert events.count(('import', 'f' * 64)) == 1
    assert first['live_model_called'] is first['public_network_called'] is False
    assert first['recorded_attempts'] == 0
    assert first['instance_id'] == second['instance_id']
    assert events.count('session_exit') == 2


def test_existing_source_checkout_runtime_needs_no_bundle(setup):
    root, events, _ = setup
    (root / 'runtime/postgres').mkdir(parents=True)
    result = mod.prepare_project(root)
    assert result['source_commit'] is None
    assert result['status'] == 'ready'
    assert not any(type(e) is tuple and e[0] == 'import' for e in events)


def test_no_bundle_no_runtime_no_download_or_init(setup):
    root, events, _ = setup
    with pytest.raises(ProjectDatabaseError, match='runtime_or_bundle_required'): mod.prepare_project(root)
    assert events == []


def test_existing_database_missing_runtime_is_never_reinstalled(setup):
    root, events, _ = setup; seed(root)
    (root / '.local/postgres').mkdir(parents=True)
    with pytest.raises(ProjectDatabaseError, match='existing_database_runtime_missing'): mod.prepare_project(root)
    assert events == []


def test_corrupt_kit_blocks_before_any_side_effect(setup, monkeypatch):
    root, events, _ = setup; seed(root)
    def broken(_): raise ProjectDatabaseError('changed')
    monkeypatch.setattr(mod, 'verify_distribution', broken)
    with pytest.raises(ProjectDatabaseError, match='changed'): mod.prepare_project(root)
    assert events == []


def test_missing_driver_fails_before_import(setup, monkeypatch):
    root, events, _ = setup; seed(root)
    monkeypatch.setattr(mod.importlib.util, 'find_spec', lambda _: None)
    with pytest.raises(ProjectDatabaseError, match='postgres_extra_required'): mod.prepare_project(root)
    assert events == []


def test_partial_database_is_not_reinitialized(setup, monkeypatch):
    root, events, DB = setup
    (root / 'runtime/postgres').mkdir(parents=True)
    (root / '.local/postgres').mkdir(parents=True)
    def invalid(self): raise ProjectDatabaseError('incomplete')
    monkeypatch.setattr(DB, 'status', invalid)
    with pytest.raises(ProjectDatabaseError, match='incomplete'): mod.prepare_project(root)
    assert events == []


def test_existing_port_cannot_silently_change(setup):
    root, events, _ = setup
    (root / 'runtime/postgres').mkdir(parents=True)
    (root / '.local/postgres').mkdir(parents=True)
    with pytest.raises(ProjectDatabaseError, match='existing_port_conflict'): mod.prepare_project(root, port=55433)
    assert 'session_enter' not in events


@pytest.mark.parametrize('port', (True, False, 0, 1023, 65536, '55432', 55432.0))
def test_invalid_port_precedes_io(setup, port):
    root, events, _ = setup
    with pytest.raises(ProjectDatabaseError, match='invalid_port'): mod.prepare_project(root, port=port)
    assert events == []


def test_runtime_version_mismatch_does_not_upgrade(setup, monkeypatch):
    root, events, _ = setup; seed(root)
    (root / 'runtime/postgres').mkdir(parents=True)
    monkeypatch.setattr(mod, 'verify_runtime', lambda _: dict(version='17.12'))
    with pytest.raises(ProjectDatabaseError, match='version_conflict'): mod.prepare_project(root)
    assert events == []


def test_windows_kit_cannot_initialize_on_wrong_platform(setup, monkeypatch):
    root, events, _ = setup; seed(root)
    def wrong(): raise ProjectDatabaseError('windows_x64_required')
    monkeypatch.setattr(mod, 'require_windows', wrong)
    with pytest.raises(ProjectDatabaseError, match='windows_x64_required'): mod.prepare_project(root)
    assert events == []
