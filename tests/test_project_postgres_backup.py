"""Physical snapshot contracts, with no real database, SQL or network."""
from copy import deepcopy
from contextlib import nullcontext
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import stat
from types import SimpleNamespace
import zipfile

import pytest

from polymarket_alpha_lab.project_postgres import backup as b, backup_format as f, files
from polymarket_alpha_lab.project_postgres.cli import main


def manifest():
    entries = {n: {'kind': 'directory'} for n in f.REQUIRED_DIRS}
    entries.update({n: {'kind': 'file', 'size': 1, 'sha256': sha256(b'x').hexdigest()} for n in f.REQUIRED_FILES})
    return dict(format=f.FORMAT, created_at='2026-09-13T00:00:00+00:00', platform=f.platform_id(),
        instance=dict(format='project-postgres-v1', instance_id='a'*32, root_sha256='b'*64,
                      system_identifier='123', version='17.11', port=55432),
        runtime_sha256='c'*64, migrations_sha256='d'*64, entries=entries)


def archive_bytes(data=None, change=None):
    data = manifest() if data is None else data
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, item in data['entries'].items():
            z.writestr(name+'/' if item['kind']=='directory' else name,
                       b'' if item['kind']=='directory' else b'x')
        z.writestr(f.MANIFEST, f.canonical(data))
        if change:
            change(z)
    return stream.getvalue()


@pytest.mark.parametrize('name', ['../data/a','/data/a','data/../x','data//x','data/./x',
    'data/a\\b','data/a:stream','data/NUL','data/CON.txt','data/LPT1','data/a.',
    'data/a ','data/a\n','data/x\0y','data/pg_tblspc/42', 'data/postmaster.pid',
    'data/standby.signal','data/recovery.signal','data/backup_label','data/tablespace_map',
    'initial-password', 'runtime/postgres/bin/postgres.exe','',None,1])
def test_unsafe_names(name):
    with pytest.raises(files.ProjectDatabaseError): f.safe_name(name)


@pytest.mark.parametrize('change', [
    lambda m:m.update(format='unknown'), lambda m:m.update(extra=1),
    lambda m:m.update(created_at='2026-09-13'),lambda m:m.update(created_at='2026-09-13T01:00:00+01:00'),
    lambda m:m.update(platform=1),lambda m:m.update(runtime_sha256='x'*64),
    lambda m:m.update(migrations_sha256='x'),lambda m:m.update(instance=[]),
    lambda m:m['instance'].update(port=True),lambda m:m['instance'].update(port=1023),
    lambda m:m['instance'].update(version='17'),lambda m:m['instance'].update(instance_id='?'),
    lambda m:m['instance'].update(system_identifier=123),lambda m:m['instance'].update(root_sha256=''),
    lambda m:m['instance'].update(other='x'),lambda m:m['instance'].update(format='other'),
    lambda m:m['entries'].pop('data/global'),lambda m:m['entries'].pop('owner.pgpass'),
    lambda m:m['entries']['app.pgpass'].update(size=True),lambda m:m['entries']['app.pgpass'].update(size=-1),
    lambda m:m['entries']['app.pgpass'].update(extra=0),lambda m:m['entries'].update({'DATA':{'kind':'directory'}}),
    lambda m:m['entries'].update({'data/file/child':{'kind':'directory'}}),
    lambda m:m['entries'].update({'data':{'kind':'file','size':1,'sha256':'a'*64}}),
])
def test_malformed_manifest_rejected(change):
    data=manifest();change(data)
    with pytest.raises(files.ProjectDatabaseError): f.parse_manifest(f.canonical(data))


def test_manifest_is_canonical_closed_and_duplicate_free():
    data=manifest();assert f.parse_manifest(f.canonical(data))==data
    for raw in (b'{"x":1,"x":2}', json.dumps(data,indent=2).encode(),b'null',b'[]',b'{"a":NaN}',b'\xff'):
        with pytest.raises(files.ProjectDatabaseError):f.parse_manifest(raw)


def test_archive_roundtrip_and_stream_hash_verification():
    with zipfile.ZipFile(BytesIO(archive_bytes())) as z:assert f.inspect_archive(z)==manifest()
    data=manifest();data['entries']['app.pgpass']['sha256']='0'*64
    with zipfile.ZipFile(BytesIO(archive_bytes(data))) as z:
        with pytest.raises(files.ProjectDatabaseError): f.inspect_archive(z)


@pytest.mark.parametrize('kind', ['duplicate','unexpected','case','link','fifo','directory_payload','trailing_slashes'])
def test_archive_wire_defects(kind):
    def change(z):
        if kind=='duplicate':z.writestr('data/PG_VERSION',b'x')
        elif kind=='unexpected':z.writestr('data/extra',b'x')
        elif kind=='case':z.writestr('DATA/',b'')
        elif kind=='directory_payload':z.writestr('data/folder/',b'x')
        elif kind=='trailing_slashes':z.writestr('data/folder//',b'')
        else:
            item=zipfile.ZipInfo('data/extra')
            item.external_attr=((stat.S_IFLNK if kind=='link' else stat.S_IFIFO)|0o600)<<16
            z.writestr(item,b'x')
    with pytest.warns(UserWarning) if kind=='duplicate' else nullcontext():
        raw=archive_bytes(change=change)
    with zipfile.ZipFile(BytesIO(raw)) as z:
        with pytest.raises(files.ProjectDatabaseError):f.inspect_archive(z)


def test_limits_apply_before_extraction(monkeypatch):
    data=manifest()
    for name,value in (('MAX_ENTRIES',1),('MAX_BYTES',1),('MAX_MANIFEST_BYTES',1)):
        with monkeypatch.context() as m:
            m.setattr(f,name,value)
            with pytest.raises(files.ProjectDatabaseError):f.parse_manifest(f.canonical(data))


@pytest.fixture
def state(tmp_path, monkeypatch):
    root=tmp_path/'Project';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (root/'database').mkdir();(root/'database/migrations.lock.json').write_text('{}')
    db=b.ProjectPostgres(root);db.layout.prepare_private();files.private_directory(db.layout.home,create=True)
    data=manifest();data['instance']['root_sha256']=db.layout.root_hash
    for name,item in sorted(data['entries'].items()):
        path=db.layout.home/name
        if item['kind']=='directory':path.mkdir(mode=0o777 if os.name=='nt' else 0o700)
        else:files.write_private(path,b'x')
    monkeypatch.setattr(b,'verify_runtime',lambda _:dict(version='17.11',files={},format='native-postgres-v1'))
    monkeypatch.setattr(b,'_migrations',lambda _:'d'*64)
    monkeypatch.setattr(b.ProjectPostgres,'_state',lambda _:deepcopy(data['instance']))
    monkeypatch.setattr(b.ProjectPostgres,'_running',lambda *_:False)
    monkeypatch.setattr(b,'_shutdown',lambda *_:None)
    return root,db.layout,data,tmp_path/'backup'


def make(state):
    root,layout,data,dest=state
    before=f.inventory(layout.home)
    result=b.create_cold_backup(root,destination=dest)
    assert f.inventory(layout.home)==before
    path=dest/'snapshot.palpg.zip'
    assert result['sha256']==sha256(path.read_bytes()).hexdigest()
    assert result['contains_credentials'] is True and result['encrypted'] is False
    return path,result['sha256']


def test_full_physical_copy_preserves_every_byte_and_empty_directory(state):
    root,layout,data,dest=state
    before=f.inventory(layout.home);path,digest=make(state)
    kwargs=dict(archive=path,expected_sha256=digest,trusted_backup=True)
    assert b.verify_cold_backup(root,**kwargs)['status']=='backup_verified'
    saved=layout.private/'original-kept';layout.home.rename(saved)
    assert b.restore_cold_backup(root,**kwargs)['status']=='restored_stopped'
    assert f.inventory(layout.home)==before==f.inventory(saved)
    assert not (layout.private/'postgres.restoring').exists()


def test_no_implicit_shutdown_or_overwrite(state,monkeypatch):
    root,layout,data,dest=state
    monkeypatch.setattr(b.ProjectPostgres,'_running',lambda *_:True)
    with pytest.raises(files.ProjectDatabaseError,match='requires_clean_shutdown'):b.create_cold_backup(root,destination=dest)
    assert not dest.exists()
    monkeypatch.setattr(b.ProjectPostgres,'_running',lambda *_:False)
    path,digest=make(state)
    with pytest.raises(files.ProjectDatabaseError,match='existing_data'):b.restore_cold_backup(root,archive=path,expected_sha256=digest,trusted_backup=True)
    with pytest.raises(files.ProjectDatabaseError,match='new_external'):b.create_cold_backup(root,destination=dest)
    with pytest.raises(files.ProjectDatabaseError,match='new_external'):b.create_cold_backup(root,destination=layout.private/'bad')


@pytest.mark.parametrize('reason',['checksum','trust','platform','root','runtime','migrations'])
def test_wrong_backup_refused_before_staging(state,monkeypatch,reason):
    root,layout,data,dest=state;path,digest=make(state)
    layout.home.rename(layout.private/'original-kept')
    kwargs=dict(archive=path,expected_sha256=digest,trusted_backup=True)
    if reason=='checksum':kwargs['expected_sha256']='0'*64
    elif reason=='trust':kwargs['trusted_backup']=False
    elif reason=='platform':monkeypatch.setattr(f,'platform_id',lambda:'wrong')
    elif reason=='root':monkeypatch.setattr(files.Layout,'root_hash',property(lambda _: '0'*64))
    elif reason=='runtime':monkeypatch.setattr(b,'verify_runtime',lambda _:dict(version='17.12'))
    elif reason=='migrations':monkeypatch.setattr(b,'_migrations',lambda _:'0'*64)
    with pytest.raises(files.ProjectDatabaseError):b.restore_cold_backup(root,**kwargs)
    assert not layout.home.exists() and not (layout.private/'postgres.restoring').exists()


def test_tampered_payload_refused_even_with_recomputed_outer_hash(state):
    root,layout,data,dest=state;path,digest=make(state)
    with zipfile.ZipFile(path) as z:contents={i.filename:z.read(i) for i in z.infolist()}
    contents['app.pgpass']=b'changed'
    with zipfile.ZipFile(path,'w') as z:
        for name,value in contents.items():z.writestr(name,value)
    layout.home.rename(layout.private/'original-kept')
    with pytest.raises(files.ProjectDatabaseError):b.restore_cold_backup(root,archive=path,
        expected_sha256=sha256(path.read_bytes()).hexdigest(),trusted_backup=True)
    assert not layout.home.exists() and not (layout.private/'postgres.restoring').exists()


def test_capture_source_change_never_publishes(state,monkeypatch):
    root,layout,data,dest=state;calls=[]
    def check(*_):
        calls.append(1)
        if len(calls)==2:files.write_private(layout.cluster/'late_file',b'changed')
    monkeypatch.setattr(b,'_shutdown',check)
    with pytest.raises(files.ProjectDatabaseError,match='source_changed'):b.create_cold_backup(root,destination=dest)
    assert not (dest/'snapshot.palpg.zip').exists()
    assert (dest/'snapshot.partial').exists()


def test_failed_staged_identity_does_not_publish_or_reset(state,monkeypatch):
    root,layout,data,dest=state;path,digest=make(state)
    layout.home.rename(layout.private/'original-kept')
    monkeypatch.setattr(b.ProjectPostgres,'_state',lambda _:dict(data['instance'],port=55433))
    with pytest.raises(files.ProjectDatabaseError):b.restore_cold_backup(root,archive=path,expected_sha256=digest,trusted_backup=True)
    assert not layout.home.exists() and (layout.private/'postgres.restoring').exists()
    assert (layout.private/'original-kept').exists()
    with pytest.raises(files.ProjectDatabaseError,match='existing_data'):b.restore_cold_backup(root,archive=path,expected_sha256=digest,trusted_backup=True)


@pytest.mark.parametrize('state',['in production','in crash recovery','shut down in recovery','starting up',''])
def test_only_clean_shutdown_control_state_accepted(tmp_path,monkeypatch,state):
    class DB:
        layout=SimpleNamespace(cluster=tmp_path)
        def _program(self,_):return '/trusted/pg_controldata'
    monkeypatch.setattr(b,'native_command',lambda *a,**k:SimpleNamespace(stdout=f'Database system identifier: 123\nDatabase cluster state: {state}\n',stderr=''))
    with pytest.raises(files.ProjectDatabaseError,match='clean_shutdown'):b._shutdown(DB(),dict(system_identifier='123'))


def test_clean_shutdown_and_crc_warning(tmp_path,monkeypatch):
    class DB:
        layout=SimpleNamespace(cluster=tmp_path)
        def _program(self,_):return '/trusted/pg_controldata'
    result=SimpleNamespace(stdout='Database system identifier: 123\nDatabase cluster state: shut down\n',stderr='')
    monkeypatch.setattr(b,'native_command',lambda *a,**k:result)
    b._shutdown(DB(),dict(system_identifier='123'))
    result.stderr='CRC warning'
    with pytest.raises(files.ProjectDatabaseError):b._shutdown(DB(),dict(system_identifier='123'))


def test_backup_lock_excludes_an_active_session(state):
    root,layout,data,dest=state
    with layout.lock():
        with pytest.raises(files.ProjectDatabaseError,match='busy'):b.create_cold_backup(root,destination=dest)
    assert not dest.exists()


def test_extra_source_link_rejected(state):
    if os.name=='nt':pytest.skip('link creation is privilege dependent on Windows')
    root,layout,data,dest=state
    (layout.cluster/'escape').symlink_to(root)
    with pytest.raises(files.ProjectDatabaseError):b.create_cold_backup(root,destination=dest)
    assert not dest.exists()


def test_source_hardlink_rejected(state):
    root,layout,data,dest=state
    os.link(layout.cluster/'PG_VERSION',layout.cluster/'hardlink')
    with pytest.raises(files.ProjectDatabaseError):b.create_cold_backup(root,destination=dest)
    assert not dest.exists()


def test_cli_help_and_error_redaction(state,monkeypatch,capsys):
    root,layout,data,dest=state
    monkeypatch.setattr(b,'verify_runtime',lambda _: (_ for _ in ()).throw(OSError('private-native-detail')))
    assert main(['--root',str(root),'backup','--destination',str(dest)])==1
    text=capsys.readouterr().err
    assert 'private-native-detail' not in text and 'backup_operation_failed' in text
    with pytest.raises(SystemExit):main(['--root',str(root),'restore','--archive','x','--sha256','a'*64])
