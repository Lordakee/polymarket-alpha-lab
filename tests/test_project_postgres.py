"""Native lifecycle contracts; no actual server, credentials or downloads."""
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import zipfile

import pytest

from polymarket_alpha_lab.project_postgres import binding, files, runtime, sql
from polymarket_alpha_lab.project_postgres.cli import main
from polymarket_alpha_lab.project_postgres.research import ProjectResearchSession
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root(tmp_path):
    p = tmp_path / 'Project With Spaces'
    p.mkdir()
    (p / 'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    (p / 'database').mkdir()
    (p / 'database/migrations.lock.json').write_text('{"format":"native-postgres-migrations-v1","migrations":[]}')
    return p


def test_status_without_initialization_has_no_side_effects(root):
    assert ProjectPostgres(root).status() == {'status': 'not_initialized'}
    assert not (root / '.local').exists()


@pytest.mark.parametrize('port', [True, 0, -1, 1023, 65536, '55432', None])
def test_invalid_ports_rejected(port):
    with pytest.raises(files.ProjectDatabaseError, match='invalid_port'):
        sql.server_configuration(port)


def test_configuration_limits_network_and_keeps_durability():
    conf = sql.server_configuration(55432)
    hba = sql.authentication_configuration()
    assert "listen_addresses = '127.0.0.1'" in conf
    assert "unix_socket_directories = ''" in conf
    assert 'fsync = on' in conf and 'full_page_writes = on' in conf and 'synchronous_commit = on' in conf
    assert 'include' not in '\n'.join(conf.splitlines()[1:])
    assert 'trust' not in hba
    assert 'local all all reject' in hba
    assert 'host all all 0.0.0.0/0 reject' in hba
    assert 'host all all ::0/0 reject' in hba
    assert 'scram-sha-256' in hba


def test_bootstrap_distinguishes_application_from_owner():
    ddl = sql.create_database_sql('1' * 64)
    assert 'NOSUPERUSER NOCREATEDB NOCREATEROLE' in ddl
    assert 'NOREPLICATION NOBYPASSRLS NOINHERIT' in ddl
    assert 'REVOKE ALL ON DATABASE postgres FROM PUBLIC' in ddl
    assert 'GRANT CONNECT ON DATABASE polymarket_alpha_lab TO pal_app' in ddl
    assert 'UPDATE' not in sql.GRANTS and 'DELETE' not in sql.GRANTS
    assert 'TRUNCATE' not in sql.GRANTS
    assert 'GRANT SELECT ON project_private.instance TO pal_app' in sql.bootstrap_sql('x','y','1')


@pytest.mark.parametrize('password', ['', '1'*63, 'x'*64, '1'*65, "a'; DROP DATABASE x; --"])
def test_only_generated_password_shape_enters_bootstrap(password):
    with pytest.raises(files.ProjectDatabaseError):
        sql.create_database_sql(password)


def test_canonical_validator_is_same_audited_function():
    from polymarket_alpha_lab.local_postgres_dsn import validate_local_postgres_dsn as new
    from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn as old
    assert new is old


def test_all_66_migrations_have_checked_in_receipts():
    rows = sql.migration_catalog(files.Layout(ROOT))
    assert len(rows) == 66
    for name, digest, body in rows:
        from polymarket_alpha_lab.project_postgres.migration_compat import native_migration_bytes
        original = (ROOT/'supabase/migrations'/name).read_bytes()
        assert digest == sha256(native_migration_bytes(name, original)).hexdigest()
        script = sql.migration_sql(name, digest, body)
        assert script.startswith('BEGIN;') and script.endswith('COMMIT;\n')
        assert f"VALUES('{name}','{digest}')" in script


@pytest.mark.parametrize('applied', [None, {}, [{'name':'wrong','sha256':'x'}],
                                   [{'name':'b','sha256':'y'}], [{'name':'a','sha256':'changed'}]])
def test_migration_history_never_guessed_or_skipped(applied):
    with pytest.raises(files.ProjectDatabaseError, match='history_conflict'):
        sql.pending_migrations((('a','x','body'),('b','y','body')), applied)


def test_migration_history_only_accepts_exact_contiguous_prefix():
    catalog=(('a','x','one'),('b','y','two'))
    assert sql.pending_migrations(catalog,[]) == catalog
    assert sql.pending_migrations(catalog,[{'name':'a','sha256':'x'}]) == catalog[1:]
    assert sql.pending_migrations(catalog,[{'name':'a','sha256':'x'},{'name':'b','sha256':'y'}]) == ()


def one_migration(root, body='CREATE TABLE t(a int);', wrapper=False):
    d=root/'supabase/migrations';d.mkdir(parents=True)
    name='20260913000000_fixture.sql'
    (d/name).write_bytes(body.encode())
    data={'format':'native-postgres-migrations-v1','migrations':[
        {'name':name,'sha256':sha256(body.encode()).hexdigest(),'transaction_wrapper':wrapper}]}
    (root/'database/migrations.lock.json').write_text(json.dumps(data))
    return d/name,data


def test_migration_bytes_cannot_change_silently(root):
    p,_=one_migration(root)
    assert len(sql.migration_catalog(files.Layout(root)))==1
    p.write_text(p.read_text()+'\n')
    with pytest.raises(files.ProjectDatabaseError, match='migration_changed'):
        sql.migration_catalog(files.Layout(root))


@pytest.mark.parametrize('defect', ['extra','missing','unknown_wrapper','path','unregistered','transaction','psql'])
def test_migration_manifest_fail_closed(root,defect):
    p,data=one_migration(root)
    if defect=='extra': data['extra']=1
    if defect=='missing': data['migrations']=[]
    if defect=='unknown_wrapper': data['migrations'][0]['transaction_wrapper']=1
    if defect=='path': data['migrations'][0]['name']='../elsewhere.sql'
    if defect=='unregistered': (p.parent/'20260913000001_other.sql').write_text('select 1;')
    if defect in ('transaction','psql'):
        body='BEGIN; select 1; COMMIT;' if defect=='transaction' else '\\! echo bad'
        p.write_text(body);data['migrations'][0]['sha256']=sha256(body.encode()).hexdigest()
    (root/'database/migrations.lock.json').write_text(json.dumps(data))
    with pytest.raises(files.ProjectDatabaseError): sql.migration_catalog(files.Layout(root))


def test_explicit_original_transaction_wrapper_is_removed_once(root):
    _,_=one_migration(root,'-- Original reviewed migration\nbegin;\ncreate table t(a int);\ncommit;\n',True)
    body=sql.migration_catalog(files.Layout(root))[0][2]
    assert 'begin;' not in body and 'commit;' not in body and 'create table' in body


def test_private_create_only_file_and_permissions(root):
    layout=files.Layout(root);layout.prepare_private()
    p=layout.private/'config'
    files.write_private(p,'test')
    assert files.read_private(p)=='test'
    with pytest.raises(FileExistsError): files.write_private(p,'replacement')
    assert files.read_private(p)=='test'
    if os.name!='nt':
        p.chmod(0o644)
        with pytest.raises(files.ProjectDatabaseError,match='permissions'): files.read_private(p)


def test_owner_lock_is_exclusive_and_released(root):
    layout=files.Layout(root)
    with layout.lock():
        with pytest.raises(files.ProjectDatabaseError,match='busy'):
            with files.Layout(root).lock(): pass
    with layout.lock(): pass


@pytest.mark.skipif(os.name=='nt',reason='Windows symlink creation needs a privileged test host')
def test_symlink_root_or_private_path_rejected(root,tmp_path):
    alias=tmp_path/'alias';alias.symlink_to(root,target_is_directory=True)
    with pytest.raises(files.ProjectDatabaseError,match='link_rejected'): files.Layout(alias)
    elsewhere=tmp_path/'elsewhere';elsewhere.mkdir()
    (root/'.local').symlink_to(elsewhere,target_is_directory=True)
    with pytest.raises(files.ProjectDatabaseError,match='link_rejected'):
        files.Layout(root).prepare_private()


@pytest.mark.parametrize('name', ['bad&root','bad%root',"bad'root",'bad\nroot'])
def test_shell_sensitive_project_paths_rejected(tmp_path,name):
    with pytest.raises(files.ProjectDatabaseError,match='unsupported_project_path'):
        files.Layout(tmp_path/name)


def test_postgres_subprocess_environment_does_not_inherit_overrides(monkeypatch):
    for k in ['PGHOST','PGSERVICE','PGPASSWORD','PGDATA','PGOPTIONS','PGPASSFILE','LD_PRELOAD','PYTHONPATH']:
        monkeypatch.setenv(k,'sentinel-private')
    env=files.clean_environment()
    assert 'sentinel-private' not in env.values()
    assert env['TZ']=='UTC' and env['LC_ALL']=='C'


def test_failed_command_does_not_expose_stderr_or_sql(monkeypatch):
    observed=[]
    def fake(args,**kw):
        observed.append((args,kw))
        return SimpleNamespace(returncode=1,stdout='sentinel-private',stderr='sentinel-secret')
    monkeypatch.setattr(files.subprocess,'run',fake)
    with pytest.raises(files.ProjectDatabaseError) as err: files.command(['explicit/exe'])
    assert str(err.value)=='project_postgres_command_failed'
    assert observed[0][1]['shell'] is False
    assert 'sentinel' not in repr(err.value)


def test_dsn_has_only_fixed_loopback_and_passfile_not_password(root):
    db=ProjectPostgres(root)
    info={'port':55432}
    dsn=db._dsn(info)
    assert "host='127.0.0.1'" in dsn and "hostaddr=" not in dsn
    assert "dbname='polymarket_alpha_lab'" in dsn and "user='pal_app'" in dsn
    assert 'app.pgpass' in dsn and 'password=' not in dsn
    assert 'passfile' not in repr(db)
    with pytest.raises(files.ProjectDatabaseError): db._dsn(info,database='other')


def test_psql_always_validates_dsn_and_uses_no_rc_or_prompt(root,monkeypatch):
    import polymarket_alpha_lab.project_postgres.server as module
    db=ProjectPostgres(root); calls=[];validations=[]
    monkeypatch.setattr(db,'_program',lambda n:'explicit/'+n)
    monkeypatch.setattr(module,'validate_local_postgres_dsn',lambda dsn,**kw:validations.append(dsn))
    monkeypatch.setattr(module,'command',lambda args,**kw:calls.append((args,kw)) or SimpleNamespace(stdout='ok\n'))
    assert db._psql({'port':55432},'SELECT 1;')=='ok'
    assert len(validations)==1
    args,kw=calls[0]
    assert '-X' in args and '-w' in args and 'ON_ERROR_STOP=1' in args
    assert 'SELECT 1' not in ' '.join(args) and 'SELECT 1' in kw['stdin']


def test_no_execution_or_fallback_for_missing_runtime(root,monkeypatch):
    called=[]
    monkeypatch.setattr(runtime,'command',lambda *a,**kw:called.append(1))
    with pytest.raises(files.ProjectDatabaseError): runtime.verify_runtime(files.Layout(root))
    assert not called


def test_wrong_archive_checksum_fails_before_any_process_or_state(root,tmp_path,monkeypatch):
    p=tmp_path/'a.zip';p.write_bytes(b'invalid zip')
    monkeypatch.setattr(runtime,'runtime_version',lambda _:pytest.fail('must not execute'))
    with pytest.raises(files.ProjectDatabaseError,match='checksum'):
        runtime.import_runtime_archive(root,p,expected_sha256='0'*64)
    assert not (root/'.local').exists()


def archive_with(names):
    bio=BytesIO()
    with zipfile.ZipFile(bio,'w') as z:
        for name in names:
            # Preserve malformed wire names: ZipInfo(name) normalizes Windows
            # backslashes before serialization, masking the negative fixture.
            item = zipfile.ZipInfo('placeholder')
            item.filename = item.orig_filename = name
            z.writestr(item, b'fixture')
    bio.seek(0)
    return zipfile.ZipFile(bio)


@pytest.mark.parametrize('name', ['../bin/exe','/pgsql/bin/exe','pgsql/../../escape',
    'pgsql/bin/a:stream','pgsql\\bin\\exe','pgsql/bin/CON','pgsql/bin/NUL.txt',
    'pgsql/bin/aux.exe','pgsql/bin/a.','pgsql/bin/a ','pgsql/bin/a\n','other/bin/exe'])
def test_unsafe_archive_paths_rejected(name):
    with archive_with([name]) as z:
        with pytest.raises(files.ProjectDatabaseError): runtime.zip_members(z)


def test_archive_filters_non_engine_components_and_preserves_notices():
    names=['pgsql/bin/postgres.exe','pgsql/lib/a.dll','pgsql/share/postgres.bki',
           'pgsql/pgAdmin/app.exe','pgsql/data/PG_VERSION','pgsql/LICENSE']
    with archive_with(names) as z:
        got=[str(p) for _,p in runtime.zip_members(z)]
    assert got==['bin/postgres.exe','lib/a.dll','share/postgres.bki','LICENSE']


def test_archive_case_collision_rejected():
    with archive_with(['pgsql/bin/A','pgsql/bin/a']) as z:
        with pytest.raises(files.ProjectDatabaseError): runtime.zip_members(z)


def test_archive_symlink_rejected():
    bio=BytesIO()
    with zipfile.ZipFile(bio,'w') as z:
        item=zipfile.ZipInfo('pgsql/bin/link');item.external_attr=(stat.S_IFLNK|0o777)<<16
        z.writestr(item,'/elsewhere')
    bio.seek(0)
    with zipfile.ZipFile(bio) as z:
        with pytest.raises(files.ProjectDatabaseError):runtime.zip_members(z)


def test_legacy_connections_unchanged_without_binding(monkeypatch):
    monkeypatch.setenv('PGHOST','legacy-fixture')
    binding.check_environment()
    binding.verify_connection(object())


@pytest.mark.parametrize('name',['PGHOST','PGPASSWORD','PGSERVICE','PGOPTIONS','pgport'])
def test_managed_connections_reject_process_env_override(name,monkeypatch):
    monkeypatch.setenv(name,'sentinel-not-printed')
    with pytest.raises(files.ProjectDatabaseError,match='environment_override') as err:
        with binding.bound('i','r','s'):pass
    assert 'sentinel' not in str(err.value)
    assert binding._EXPECTED.get() is None


def test_identity_is_checked_inside_each_research_transaction():
    class Cursor:
        def execute(self,s):self.sql=s
        def fetchall(self):return [('i','r','s','polymarket_alpha_lab','pal_app')]
    c=Cursor()
    with binding.bound('i','r','s'):
        binding.verify_connection(c)
        assert 'project_private.instance' in c.sql
        with binding.bound('different','r','s'):
            with pytest.raises(files.ProjectDatabaseError):binding.verify_connection(c)
        binding.verify_connection(c)
    assert binding._EXPECTED.get() is None


def test_session_methods_are_bound_and_expire(root,monkeypatch):
    import polymarket_alpha_lab.research_execution_psycopg as execution
    db=ProjectPostgres(root)
    info={'port':55432,'instance_id':'i','root_sha256':'r','system_identifier':'s'}
    session=ProjectResearchSession(db,info)
    calls=[]
    def fake(dsn,**kw):
        calls.append((binding._EXPECTED.get(),kw))
        return 'captured'
    monkeypatch.setattr(execution,'run_captured_research_with_psycopg',fake)
    assert session.run_research(request='request',model_factory='model')=='captured'
    assert calls[0][0]==('i','r','s')
    assert 'app.pgpass' not in repr(session)
    session.close()
    with pytest.raises(files.ProjectDatabaseError,match='session_closed'):
        session.run_research(request='request',model_factory='model')
    assert len(calls)==1


def test_init_refuses_existing_data_before_initdb(root,monkeypatch):
    import polymarket_alpha_lab.project_postgres.server as module
    db=ProjectPostgres(root);db.layout.prepare_private()
    db.layout.home.mkdir(mode=0o700)
    (db.layout.home/'sentinel').write_text('existing data')
    monkeypatch.setattr(module,'verify_runtime',lambda _: {'version':'16.15'})
    monkeypatch.setattr(sql,'migration_catalog',lambda _: ())
    monkeypatch.setattr(module,'command',lambda *a,**kw:pytest.fail('must not initialize'))
    with pytest.raises(files.ProjectDatabaseError,match='existing_data'):
        db.initialize()
    assert (db.layout.home/'sentinel').read_text()=='existing data'


def test_cli_errors_are_fixed_and_never_dump_a_traceback(root,monkeypatch,capsys):
    monkeypatch.setattr(ProjectPostgres,'up',lambda _: (_ for _ in ()).throw(RuntimeError('sentinel-secret')))
    assert main(['--root',str(root),'up'])==1
    out=capsys.readouterr()
    assert 'sentinel' not in out.err and 'Traceback' not in out.err and out.out==''
    assert json.loads(out.err)['reason_code']=='project_postgres_operation_failed'


def test_cli_no_implicit_install_init_or_start(root,capsys):
    assert main(['--root',str(root),'status'])==0
    assert json.loads(capsys.readouterr().out)['status']=='not_initialized'
    assert not (root/'.local').exists()


def instance_fixture(root,monkeypatch):
    from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
    db=ProjectPostgres(root);layout=db.layout
    layout.prepare_private();files.private_directory(layout.home,create=True)
    files.private_directory(layout.cluster,create=True)
    info=dict(format='project-postgres-v1',instance_id='1'*32,root_sha256=layout.root_hash,
              system_identifier='123456789',version='17.11',port=55432)
    for name,value in {'instance.json':json.dumps(info),'initialized':info['instance_id'],
        'owner.pgpass':'127.0.0.1:55432:*:pal_owner:'+'2'*64+'\n',
        'app.pgpass':'127.0.0.1:55432:*:pal_app:'+'3'*64+'\n'}.items():
        files.write_private(layout.home/name,value)
    for name,value in {'PG_VERSION':'17\n','postgresql.conf':sql.server_configuration(55432),
        'pg_hba.conf':sql.authentication_configuration(),'postgresql.auto.conf':'# Managed default\n'}.items():
        files.write_private(layout.cluster/name,value)
    monkeypatch.setattr(db,'_disk_identifier',lambda:'123456789')
    return db,info


@pytest.mark.parametrize('field,value',[('root_sha256','0'*64),('system_identifier','9'),
    ('instance_id','bad'),('port',True),('port',65536),('version','18.0'),('format','unknown')])
def test_private_state_never_adopts_other_cluster_or_project(root,monkeypatch,field,value):
    db,info=instance_fixture(root,monkeypatch)
    assert db._state()==info
    info[field]=value
    (db.layout.home/'instance.json').write_text(json.dumps(info))
    with pytest.raises(files.ProjectDatabaseError):db._state()


@pytest.mark.parametrize('filename,extra',[('postgresql.conf',"listen_addresses='*'\n"),
    ('pg_hba.conf','host all all 0.0.0.0/0 trust\n'),('postgresql.auto.conf',"port='5432'\n")])
def test_native_config_override_never_silently_repaired(root,monkeypatch,filename,extra):
    db,info=instance_fixture(root,monkeypatch)
    p=db.layout.cluster/filename;p.write_text(p.read_text()+extra)
    with pytest.raises(files.ProjectDatabaseError,match='configuration_changed'):db._state()
    assert extra in p.read_text()


def test_missing_ready_marker_never_reinitializes_partial_cluster(root,monkeypatch):
    db,info=instance_fixture(root,monkeypatch)
    (db.layout.home/'initialized').unlink()
    with pytest.raises(files.ProjectDatabaseError,match='incomplete'):db._state()
    assert db._state(ready=False)==info  # explicit safe stop can inspect partial initialization


def test_runtime_import_copies_only_native_programs_not_user_cluster(root,tmp_path,monkeypatch):
    source=tmp_path/'trusted-prefix';source.mkdir()
    for name in ('bin','lib','share'):
        (source/name).mkdir();(source/name/'fixture').write_text('trusted synthetic file')
    (source/'data').mkdir();(source/'data'/'credentials').write_text('never-copy-this')
    (source/'LICENSE').write_text('Synthetic license fixture')
    monkeypatch.setattr(runtime,'runtime_version',lambda _: '17.11')
    assert runtime.import_runtime_directory(root,source)=='17.11'
    layout=files.Layout(root)
    assert not (layout.runtime/'data').exists()
    assert (layout.runtime/'LICENSE').is_file()
    assert runtime.verify_runtime(layout)['version']=='17.11'
    (layout.runtime/'bin'/'fixture').write_text('changed')
    with pytest.raises(files.ProjectDatabaseError,match='runtime_changed'):runtime.verify_runtime(layout)
    with pytest.raises(files.ProjectDatabaseError,match='already_installed'):
        runtime.import_runtime_directory(root,source)


@pytest.mark.parametrize('started',[True,False])
def test_session_only_stops_a_server_it_started(root,monkeypatch,started):
    import polymarket_alpha_lab.project_postgres.server as module
    db=ProjectPostgres(root);stopped=[]
    info=dict(version='17.11',instance_id='i',root_sha256='r',system_identifier='s',port=55432)
    monkeypatch.setattr(module,'verify_runtime',lambda _: {'version':'17.11'})
    monkeypatch.setattr(db,'_state',lambda:info)
    monkeypatch.setattr(db,'_start',lambda _:started)
    monkeypatch.setattr(db,'_pending',lambda _:())
    monkeypatch.setattr(db,'_stop',lambda _:stopped.append(1))
    with pytest.raises(ValueError,match='fixture'):
        with db.session() as session:raise ValueError('fixture')
    assert stopped==([1] if started else [])
    with pytest.raises(files.ProjectDatabaseError,match='session_closed'):
        session.inspect(record_id='anything')


def test_stop_refuses_active_connections_and_never_force_kills(root,monkeypatch):
    db=ProjectPostgres(root);events=[]
    monkeypatch.setattr(db,'_running',lambda _:True)
    monkeypatch.setattr(db,'_server_identity',lambda *a,**kw:events.append('identity'))
    monkeypatch.setattr(db,'_psql',lambda *a,**kw:'1')
    monkeypatch.setattr(db,'_control',lambda *a,**kw:pytest.fail('must not stop'))
    with pytest.raises(files.ProjectDatabaseError,match='connections_active'):db._stop({})
    assert events==['identity']


def test_session_close_waits_for_active_research_not_just_db_connections(root):
    from threading import Event, Thread
    db=ProjectPostgres(root)
    info=dict(port=55432,instance_id='i',root_sha256='r',system_identifier='s')
    session=ProjectResearchSession(db,info)
    entered,release,closed=Event(),Event(),Event()
    def work(dsn):entered.set();assert release.wait(5);return 'finished'
    worker=Thread(target=lambda:session._call(work));worker.start();assert entered.wait(5)
    closer=Thread(target=lambda:(session.close(),closed.set()));closer.start()
    try:
        assert not closed.wait(.05)
    finally:
        release.set();worker.join(5);closer.join(5)
    assert closed.is_set() and not worker.is_alive() and not closer.is_alive()
