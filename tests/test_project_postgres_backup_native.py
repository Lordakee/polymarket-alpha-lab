"""Real cold-backup/recovery proof on a NEW private native Windows cluster.

Only synthetic records are written. Original directories are retained during
simulated loss; no user's database or backup is opened, changed or uploaded.
"""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import shutil
import socket
import time
import uuid

import pytest

from polymarket_alpha_lab.project_postgres.backup import (
    create_cold_backup, restore_cold_backup, verify_cold_backup,
)
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError, digest_file, private_directory
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from tests.test_project_postgres_native import Model, request, ROOT

ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_BACKUP') == '1'


@pytest.mark.skipif(not ENABLED, reason='explicit private native backup proof is opt-in')
def test_native_cold_backup_recovery_preserves_prospective_history(tmp_path, monkeypatch):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):
            monkeypatch.delenv(key)
    if os.name == 'nt':
        base = Path(os.environ['RUNNER_TEMP']) / ('pal-backup-' + uuid.uuid4().hex)
        private_directory(base, create=True)
    else:
        base = tmp_path
    root = base / 'Project With Spaces'
    root.mkdir()
    (root / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT / 'database', root / 'database')
    shutil.copytree(ROOT / 'supabase/migrations', root / 'supabase/migrations')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    import_runtime_directory(root, prefix)
    db = ProjectPostgres(root)
    db.initialize(port=port)
    print('native backup: initialized private cluster with all historical migrations')
    try:
        with db.session() as session:
            cutoff = datetime.now(UTC) + timedelta(seconds=12)
            first = replace(request(101), forecast_cutoff_at=cutoff)
            captured = session.run_research(request=first, model_factory=lambda _: Model())
            assert captured.status == 'captured'
            second = request(102)
            def failed_model(_):
                raise RuntimeError('synthetic model factory failure')
            failed = session.run_research(request=second, model_factory=failed_model)
            assert failed.status == 'captured' and failed.record.run.research.status == 'failed'
            while datetime.now(UTC) <= cutoff:
                time.sleep(0.05)
            session.capture_outcome(condition_id=first.intake.condition_id,
                market_slug=first.intake.market_slug, resolved_at=datetime.now(UTC), actual_yes=True,
                source_reference='synthetic:confirmed-native-backup', source_content_sha256='a'*64)
            at = datetime.now(UTC)
            before = session.evaluate(generated_at=at).to_dict()
        identity = db._state()
        credentials = tuple(digest_file(db.layout.home / n) for n in ('owner.pgpass', 'app.pgpass'))
        destination = base / 'Private Backup'
        receipt = create_cold_backup(root, destination=destination)
        args = dict(archive=destination / 'snapshot.palpg.zip', expected_sha256=receipt['sha256'], trusted_backup=True)
        assert verify_cold_backup(root, **args)['status'] == 'backup_verified'
        assert db.status()['status'] == 'stopped'
        assert db.up()['status'] == 'running'
        with pytest.raises(ProjectDatabaseError, match='requires_clean_shutdown'):
            create_cold_backup(root, destination=base / 'Must Not Exist')
        assert not (base / 'Must Not Exist').exists()
        assert db.status()['status'] == 'running'
        db.down()
        with pytest.raises(ProjectDatabaseError, match='existing_data'):
            restore_cold_backup(root, **args)
        # Simulate unavailable original files WITHOUT deleting any original data.
        db.layout.home.rename(base / 'Original Preserved')
        bad = dict(args, expected_sha256='0'*64)
        with pytest.raises(ProjectDatabaseError, match='checksum_mismatch'):
            restore_cold_backup(root, **bad)
        assert not db.layout.home.exists()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', port)); sock.listen()
            with pytest.raises(ProjectDatabaseError, match='port_in_use'):
                restore_cold_backup(root, **args)
        assert not (db.layout.private / 'postgres.restoring').exists()
        assert restore_cold_backup(root, **args)['status'] == 'restored_stopped'
        assert db.status()['status'] == 'stopped' and db._state() == identity
        credentials_preserved = tuple(digest_file(db.layout.home / n) for n in ('owner.pgpass', 'app.pgpass')) == credentials
        assert credentials_preserved  # No generated credential text in assertions/logs.
        with db.session() as session:
            assert session.inspect(record_id=first.record_id).record == captured.record
            assert session.inspect(record_id=second.record_id).record == failed.record
            assert session.evaluate(generated_at=at).to_dict() == before
            def forbidden(_):
                pytest.fail('completed replay must not call the model')
            assert session.run_research(request=first, model_factory=forbidden).record == captured.record
            with pytest.raises(ProjectDatabaseError):
                db._psql(identity, 'DELETE FROM research_capture.attempts;', owner=False)
            third = request(103)
            def interrupted(_):
                raise KeyboardInterrupt('synthetic interruption')
            with pytest.raises(KeyboardInterrupt):
                session.run_research(request=third, model_factory=interrupted)
            assert session.inspect(record_id=third.record_id).status == 'incomplete'
            with pytest.raises(Exception, match='incomplete'):
                session.evaluate()
        print('native backup: records, outcome, original clocks, score and role restrictions preserved')
        destination2 = base / 'Incomplete History Backup'
        receipt2 = create_cold_backup(root, destination=destination2)
        db.layout.home.rename(base / 'Incomplete Original Preserved')
        restore_cold_backup(root, archive=destination2 / 'snapshot.palpg.zip', expected_sha256=receipt2['sha256'], trusted_backup=True)
        with db.session() as session:
            assert session.inspect(record_id=third.record_id).status == 'incomplete'
            with pytest.raises(Exception, match='incomplete'):
                session.evaluate()
        print('native backup: PASS; incomplete claims remain visible; no reset, SQL replay or Docker')
    finally:
        if db.layout.home.exists():
            db.down()
