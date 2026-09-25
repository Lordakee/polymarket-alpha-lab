"""Preparation package refusal tests; no real CLI, global install, or VM launch."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import types
import xml.etree.ElementTree as ET
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('probe_environment', ROOT/'scripts/claude_probe_environment.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)


def payload(tmp_path):
    root = tmp_path/'payload'; root.mkdir()
    (root/'smoke.cmd').write_bytes(e.SMOKE_CMD)
    (root/'source').mkdir(); (root/'source/synthetic.py').write_bytes(b'# synthetic source\n')
    m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
    (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    return root, m


def archive(tmp_path, names=None):
    path = tmp_path/'test.zip'
    with zipfile.ZipFile(path, 'x') as z:
        if names is None:
            root, _ = payload(tmp_path)
            for name, f in e.walk(root).items(): z.write(f, name)
        else:
            for name in names: z.writestr(name, b'synthetic')
    return path, sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('name', ['../a','/a','C:/a','a\\b','a/../b','a//b','a/./b','a/','a:stream',
                                  'a/CON.txt','a/NUL','LPT1.log','a.','a ','a\nb','a%/\x00','中.txt'])
def test_hostile_bundle_names_rejected(name):
    with pytest.raises(ValueError): e.clean_name(name)


@pytest.mark.parametrize('name', ['python/Lib/json/__init__.py','source/src/package.py',
                                  'python/Lib/site-packages/pytest-9.0.2.dist-info/licenses/LICENSE'])
def test_regular_portable_names(name):
    assert e.clean_name(name).as_posix() == name


def test_verified_payload_is_not_an_activation_certificate(tmp_path):
    root, m = payload(tmp_path)
    assert e.verify(root) == m
    assert m['official_cli_included'] is m['activation_authorized'] is False


@pytest.mark.parametrize('fault', ['changed','extra','removed','duplicate','wrong_size','wrong_flag','duplicate_json'])
def test_modified_manifest_or_payload_refused(tmp_path, fault):
    root, m = payload(tmp_path)
    if fault == 'changed': (root/'smoke.cmd').write_bytes(b'changed')
    if fault == 'extra': (root/'unexpected.txt').write_bytes(b'')
    if fault == 'removed': (root/'smoke.cmd').unlink()
    if fault == 'duplicate': m['files'].append(m['files'][0])
    if fault == 'wrong_size': m['files'][0]['bytes'] = True
    if fault == 'wrong_flag': m['activation_authorized'] = True
    text = json.dumps(m)
    if fault == 'duplicate_json': text = text.replace('"schema":', '"schema":"duplicate","schema":', 1)
    (root/'environment-manifest.json').write_text(text, encoding='utf-8')
    with pytest.raises(ValueError): e.verify(root)


def test_stage_has_two_new_narrow_maps_and_no_launch(monkeypatch,tmp_path):
    z, h = archive(tmp_path)
    monkeypatch.setattr(subprocess, 'run', lambda *a,**k: pytest.fail('process launched'))
    destination = tmp_path/'new-stage'
    result = e.stage(z,h,destination)
    assert result['status'] == 'staged_not_launched'
    doc = ET.fromstring((destination/'preparation-smoke.wsb').read_bytes())
    for tag in ('Networking','ClipboardRedirection','vGPU','AudioInput','VideoInput','PrinterRedirection'):
        assert doc.findtext(tag) == 'Disable'
    assert doc.findtext('ProtectedClient') == 'Enable'
    maps = doc.findall('MappedFolders/MappedFolder')
    assert [(m.findtext('HostFolder'),m.findtext('ReadOnly')) for m in maps] == [
        (str(destination/'input'),'true'),(str(destination/'output'),'false')]
    assert list((destination/'output').iterdir()) == []
    assert 'powershell' not in doc.findtext('LogonCommand/Command').lower()
    assert e.verify(destination/'input')['source_commit'] == 'a'*40


def test_stage_never_overwrites_existing_directory(tmp_path):
    z,h=archive(tmp_path);destination=tmp_path/'existing';destination.mkdir()
    marker=destination/'kept';marker.write_bytes(b'keep')
    with pytest.raises(ValueError,match='destination_exists'): e.stage(z,h,destination)
    assert marker.read_bytes() == b'keep' and list(destination.iterdir()) == [marker]


def test_bad_archive_hash_creates_nothing(tmp_path):
    z,_=archive(tmp_path);target=tmp_path/'stage'
    with pytest.raises(ValueError,match='archive_hash_mismatch'):e.stage(z,'0'*64,target)
    assert not target.exists()


@pytest.mark.parametrize('names',[['../escape'],['a','A'],['file:ads'],['/absolute']])
def test_unsafe_zip_refused_before_writing(tmp_path,names):
    z,h=archive(tmp_path,names);target=tmp_path/'stage'
    with pytest.raises(ValueError):e.stage(z,h,target)
    assert not target.exists()


def test_symlink_zip_refused(tmp_path):
    path=tmp_path/'link.zip'
    with zipfile.ZipFile(path,'x') as z:
        info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
        z.writestr(info,'outside')
    with pytest.raises(ValueError):e.stage(path,sha256(path.read_bytes()).hexdigest(),tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_manifest_failure_retains_attempt_and_does_not_generate_launcher(tmp_path):
    z,h=archive(tmp_path,['random']);target=tmp_path/'stage'
    with pytest.raises(ValueError):e.stage(z,h,target)
    assert (target/'input/random').read_bytes()==b'synthetic'
    assert not (target/'preparation-smoke.wsb').exists()


def test_expanding_mapping_path_rejected_before_creation(tmp_path):
    z,h=archive(tmp_path)
    with pytest.raises(ValueError,match='mapping_path_invalid'):e.stage(z,h,tmp_path/'%TEMP%')
    assert not (tmp_path/'%TEMP%').exists()


def test_xml_escapes_paths_without_expanding_scope():
    doc=ET.fromstring(e.sandbox_xml(Path('C:/clean & dedicated/input'),Path('C:/clean & dedicated/output')))
    assert doc.findtext('MappedFolders/MappedFolder/HostFolder')==str(Path('C:/clean & dedicated/input'))
    assert len(doc.findall('MappedFolders/MappedFolder'))==2


def test_build_on_user_machine_refused_before_reads(monkeypatch,tmp_path):
    monkeypatch.delenv('GITHUB_ACTIONS',raising=False)
    with pytest.raises(ValueError,match='ci_build_only'):e.build(tmp_path,tmp_path/'out',True)
    assert not (tmp_path/'out').exists()


def test_host_script_is_ascii_and_has_no_mutating_or_vendor_commands():
    text=(ROOT/'scripts/inspect_claude_probe_host.ps1').read_text(encoding='ascii')
    for bad in ('Enable-WindowsOptionalFeature','Set-NetFirewall','Start-Process','Invoke-WebRequest',
                'Get-ChildItem','Get-Content','uv sync','credential.helper','--version','RunAs'):
        assert bad not in text
    assert "Name='Containers-DisposableClientVM'" in text


@pytest.mark.skipif(sys.platform!='win32',reason='PowerShell 5.1 synthetic host query proof')
@pytest.mark.parametrize('state,expected', [(1,'review_prepared_sandbox_smoke'),(2,'operator_decision_required'),
                                          (3,'operator_decision_required'),(4,'operator_decision_required')])
def test_actual_powershell_queries_never_require_clean_parent_or_uv(tmp_path,state,expected):
    host=ROOT/'scripts/inspect_claude_probe_host.ps1'
    code=f"""
. '{str(host).replace("'", "''")}'
function Get-ItemProperty {{ [pscustomobject]@{{EditionID='Professional'}} }}
function Get-CimInstance {{
 param($ClassName,$Filter,$Property)
 switch ($ClassName) {{
  'Win32_OptionalFeature' {{ [pscustomobject]@{{InstallState={state}}} }}
  'Win32_Processor' {{ [pscustomobject]@{{VirtualizationFirmwareEnabled=$true}} }}
  'Win32_ComputerSystem' {{ [pscustomobject]@{{HypervisorPresent=$true}} }}
  default {{ throw 'unexpected query' }}
 }}
}}
Get-ProbeHostFacts | ConvertTo-Json -Compress
"""
    shell=Path(__import__('os').environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    child=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-Command',code],capture_output=True,text=True,timeout=30)
    assert child.returncode==0,child.stderr
    result=json.loads(child.stdout)
    assert result['next_action']==expected and result['reads_failed']==[]
    assert result['vendor_executed'] is result['global_tools_changed'] is False


def test_dot_is_not_an_archive_member():
    with pytest.raises(ValueError, match='invalid_bundle_path'): e.clean_name('.')


@pytest.mark.parametrize('kind',[stat.S_IFIFO,stat.S_IFSOCK,stat.S_IFCHR])
def test_special_file_metadata_rejected_before_destination(tmp_path,kind):
    z=tmp_path/'special.zip'
    with zipfile.ZipFile(z,'x') as out:
        info=zipfile.ZipInfo('special');info.create_system=3;info.external_attr=(kind|0o600)<<16
        out.writestr(info,b'data')
    destination=tmp_path/'stage'
    with pytest.raises(ValueError,match='archive_entry_invalid'):
        e.stage(z,sha256(z.read_bytes()).hexdigest(),destination)
    assert not destination.exists()


def test_unreadable_walk_never_silently_certifies_partial_inventory(monkeypatch,tmp_path):
    root,_=payload(tmp_path)
    original=e.os.walk
    def failing_walk(path,**kwargs):
        callback=kwargs.get('onerror')
        if callback is not None: callback(PermissionError('synthetic unreadable subtree'))
        yield from original(path,**kwargs)
    monkeypatch.setattr(e.os,'walk',failing_walk)
    with pytest.raises(OSError):e.verify(root)


def test_committed_source_bytes_survive_windows_checkout_eol_conversion(tmp_path):
    repository = tmp_path/'git-source'; repository.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(repository),'-c','core.autocrlf=true',*args],
                                       stderr=subprocess.PIPE)
    git('init')
    names = ('src/sample.py', *e.SOURCE_EXTRA)
    for name in names:
        target=repository/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b'# committed LF\nsecond line\n')
    git('add','.')
    git('-c','user.name=Fixture','-c','user.email=fixture@invalid','commit','-m','synthetic source')
    for name in names:
        (repository/name).write_bytes(b'# committed LF\r\nsecond line\r\n')
    # Compare content after Git's own EOL conversion, not transient index stat cache.
    assert git('diff','--exit-code')==b''
    selected=dict(e.committed_source_files(git))
    assert set(selected)==set(names)
    assert all(data==b'# committed LF\nsecond line\n' for data in selected.values())


def test_export_substitution_cannot_silently_change_committed_bytes(tmp_path):
    repository=tmp_path/'git-source';repository.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(repository),*args],stderr=subprocess.PIPE)
    git('init')
    for name in ('src/sample.py', *e.SOURCE_EXTRA):
        target=repository/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b'# $Format:%H$\n')
    (repository/'.gitattributes').write_bytes(b'src/sample.py export-subst\n')
    git('add','.')
    git('-c','user.name=Fixture','-c','user.email=fixture@invalid','commit','-m','synthetic export substitution')
    with pytest.raises(ValueError,match='source_changed'):
        tuple(e.committed_source_files(git))


# --- Official control/configuration generation (offline stand-ins only) ---

OFFICIAL_IMAGE_DATA = b'PAL synthetic claude.exe stand-in; never executed by tests.\n'*160
OFFICIAL_PROBE_VARS = (
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE', '1'),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE', r'C:\pal-claude-image\claude.exe'),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256', sha256(OFFICIAL_IMAGE_DATA).hexdigest()),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES', str(len(OFFICIAL_IMAGE_DATA))),
    ('POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST', '1'),
)


def official_payload(parent, name='payload', complete=True):
    """Richer preparation stand-in covering the launcher-required layout."""
    root = parent/name; root.mkdir()
    (root/'smoke.cmd').write_bytes(e.SMOKE_CMD)
    (root/'source').mkdir(); (root/'source/synthetic.py').write_bytes(b'# synthetic source\n')
    (root/'source/src').mkdir(); (root/'source/src/pkg.py').write_bytes(b'# package code\n')
    (root/'source/tests').mkdir()
    (root/'source/tests/test_research_claude_profile_native.py').write_bytes(b'# native stand-in\n')
    if complete:
        (root/'python/Lib/site-packages').mkdir(parents=True)
        (root/'python/Lib/site-packages/pytest-stub.py').write_bytes(b'# pytest stand-in\n')
        (root/'python/python.exe').write_bytes(b'MZ synthetic bundled python; never executed\n')
    m = e.manifest(root, 'a'*40, 'b'*40, {'pytest': '9.0.2'})
    (root/'environment-manifest.json').write_text(json.dumps(m), encoding='utf-8')
    return root, m


def valid_manifest(data=OFFICIAL_IMAGE_DATA):
    return dict(schema='claude-probe-image-v1', path='claude.exe',
                sha256=sha256(data).hexdigest(), bytes=len(data), version='2.1.278')


def write_image(parent, name, value, *, raw=None, data=OFFICIAL_IMAGE_DATA, inventory=None):
    image = parent/name; image.mkdir()
    (image/'claude.exe').write_bytes(data)
    text = json.dumps(value) if raw is None else raw
    (image/'image-manifest.json').write_text(text, encoding='utf-8')
    for extra in inventory or ():
        (image/extra).write_bytes(b'unexpected')
    return image


def official_image(parent, name='image'):
    return write_image(parent, name, valid_manifest())


def official_setup(tmp_path):
    root, _ = official_payload(tmp_path)
    image = official_image(tmp_path)
    control = tmp_path/'control'
    e.official_control(image, control)
    return root, image, control


def image_snapshot(image):
    return {p.name: p.read_bytes() for p in image.iterdir()}


def test_official_config_four_mappings_and_hardening(tmp_path):
    root, image, control = official_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.wsb'
    e.official_config(root, image, control, output, destination, isolated_host_attested=True)
    doc = ET.fromstring(destination.read_bytes())
    for tag in ('Networking','ClipboardRedirection','vGPU','AudioInput','VideoInput','PrinterRedirection'):
        assert doc.findtext(tag) == 'Disable'
    assert doc.findtext('ProtectedClient') == 'Enable'
    assert doc.findtext('MemoryInMB') == '4096'
    maps = doc.findall('MappedFolders/MappedFolder')
    assert [(m.findtext('HostFolder'),m.findtext('SandboxFolder'),m.findtext('ReadOnly')) for m in maps] == [
        (str(root), r'C:\pal-input', 'true'),
        (str(image), r'C:\pal-claude-image', 'true'),
        (str(control), r'C:\pal-control', 'true'),
        (str(output), r'C:\pal-output', 'false')]
    assert len(maps) == 4
    assert doc.findtext('LogonCommand/Command') == (
        r'C:\Windows\System32\cmd.exe /d /c C:\pal-control\official-probe.cmd --isolated-host-attested')
    assert list(output.iterdir()) == []


def test_official_config_xml_is_ascii_and_escapes_paths(tmp_path):
    root, _ = official_payload(tmp_path, 'p\u00e4yload & in')
    image = official_image(tmp_path, 'im\u00e4ge dir')
    control = tmp_path/'c\u00f6ntrol'
    e.official_control(image, control)
    output = tmp_path/'o\u00fctput'; destination = tmp_path/'official probe.wsb'
    e.official_config(root, image, control, output, destination, isolated_host_attested=True)
    raw = destination.read_bytes()
    assert all(byte < 128 for byte in raw)
    doc = ET.fromstring(raw)
    assert [m.findtext('HostFolder') for m in doc.findall('MappedFolders/MappedFolder')] == [
        str(root), str(image), str(control), str(output)]
    direct = e.official_sandbox_xml(Path('C:\\ro\\oms & d\u00e9cor'), Path('C:\\ro\\im\u00e4ge'),
                                    Path('C:\\ro\\c\u00f6ntrol'), Path('C:\\ro\\o\u00fctput'))
    assert all(byte < 128 for byte in direct)
    assert [m.findtext('HostFolder') for m in ET.fromstring(direct).findall('MappedFolders/MappedFolder')] == [
        'C:\\ro\\oms & d\u00e9cor', 'C:\\ro\\im\u00e4ge', 'C:\\ro\\c\u00f6ntrol', 'C:\\ro\\o\u00fctput']


def test_official_launcher_has_exact_native_probe_contract():
    manifest = valid_manifest()
    text = e.official_launcher(manifest).decode('ascii')
    for name, value in OFFICIAL_PROBE_VARS:
        assert f'set "{name}={value}"' in text
    assert '"C:\\pal-input\\python\\python.exe" -I -S -B -c ' in text
    assert ("sys.path[:0]=[r'C:\\pal-input\\source',r'C:\\pal-input\\source\\src',"
            "r'C:\\pal-input\\python\\Lib\\site-packages']") in text
    for option in ("'-q'","'-s'","'--tb=short'","'junit_family=legacy'","'no:cacheprovider'",
                   r"'--basetemp=C:\pal-output\pytest-tmp'", r"'--junitxml=C:\pal-output\junit.xml'",
                   r"'C:\pal-input\source\tests\test_research_claude_profile_native.py'"):
        assert option in text
    assert "receipt=open(r'C:\\pal-output\\exit-code.txt','x',encoding='ascii')" in text
    assert "raise SystemExit(code)" in text
    assert len({name for name, _ in OFFICIAL_PROBE_VARS}) == 5


def test_official_launcher_is_ascii_and_guards_first_attempt():
    manifest = valid_manifest()
    data = e.official_launcher(manifest)
    assert b'\r\n' in data and b'\n' not in data.replace(b'\r\n', b'')
    assert not data.startswith(b'\xef\xbb\xbf')
    assert b'{' not in data
    lines = data.decode('ascii').split('\r\n')
    assert max(len(line) for line in lines) < 8191
    assert lines[2] == 'if not "%~1"=="--isolated-host-attested" exit /b 2'
    assert lines[3] == 'if not "%~2"=="" exit /b 2'
    assert lines[4] == 'if not "%*"=="--isolated-host-attested" exit /b 2'
    redir = next(i for i, line in enumerate(lines) if '>"C:\\pal-output\\pytest.log"' in line)
    guards = ['mkdir "C:\\pal-output\\launcher-tmp"', 'if errorlevel 1 exit /b 2']
    guards += [f'if exist "C:\\pal-output\\{n}" exit /b 2'
               for n in ('launcher-tmp','pytest-tmp','pytest.log','junit.xml','exit-code.txt')]
    assert all(lines.index(guard) < redir for guard in guards)
    for fault in ({'sha256': 'A'*64}, {'sha256': 'a'*63}, {'sha256': 12345},
                  {'bytes': True}, {'bytes': 0}, {'bytes': -1}, {'bytes': 1.5},
                  {'bytes': 536870913}):
        with pytest.raises(ValueError):
            e.official_launcher({**valid_manifest(), **fault})


def test_official_generation_never_starts_processes(monkeypatch,tmp_path):
    def launched(*args, **kwargs):
        pytest.fail('process launched')
    monkeypatch.setattr(subprocess, 'run', launched)
    monkeypatch.setattr(subprocess, 'check_output', launched)
    monkeypatch.setattr(subprocess, 'Popen', launched)
    monkeypatch.setattr(os, 'system', launched, raising=False)
    monkeypatch.setattr(os, 'startfile', launched, raising=False)
    root, image, control = official_setup(tmp_path)
    assert e.official_control(image, tmp_path/'control2')['official_cli_executed'] is False
    assert e.official_config(root, image, control, tmp_path/'output2',
                             tmp_path/'official2.wsb',
                             isolated_host_attested=True)['activation_authorized'] is False
    monkeypatch.setattr(sys, 'argv', ['probe', 'official-control', '--image-dir', str(image),
                                      '--destination', str(tmp_path/'control3')])
    assert e.main() == 0
    monkeypatch.setattr(sys, 'argv', ['probe', 'official-config', '--payload-root', str(root),
                                      '--image-dir', str(image), '--control-dir', str(tmp_path/'control3'),
                                      '--output-dir', str(tmp_path/'output3'),
                                      '--destination', str(tmp_path/'official3.wsb'),
                                      '--isolated-host-attested'])
    assert e.main() == 0
    assert (tmp_path/'output3').is_dir() and (tmp_path/'official3.wsb').is_file()


def test_official_generation_preserves_preparation_payload(tmp_path):
    root, m = official_payload(tmp_path)
    before = {p.relative_to(root).as_posix(): p.read_bytes()
              for p in root.rglob('*') if p.is_file()}
    z_path = tmp_path/'prep.zip'
    with zipfile.ZipFile(z_path, 'x') as z:
        for name, f in e.walk(root).items(): z.write(f, name)
    e.stage(z_path, sha256(z_path.read_bytes()).hexdigest(), tmp_path/'stage-attempt')
    prep_wsb = (tmp_path/'stage-attempt'/'preparation-smoke.wsb').read_bytes()
    image = official_image(tmp_path); control = tmp_path/'control'
    e.official_control(image, control)
    e.official_config(root, image, control, tmp_path/'official-output',
                      tmp_path/'official-probe.wsb', isolated_host_attested=True)
    after = {p.relative_to(root).as_posix(): p.read_bytes()
             for p in root.rglob('*') if p.is_file()}
    assert after == before
    assert (root/'smoke.cmd').read_bytes() == e.SMOKE_CMD
    assert e.verify(root) == m
    assert (tmp_path/'stage-attempt'/'preparation-smoke.wsb').read_bytes() == prep_wsb
    assert (control/'official-probe.cmd').read_bytes() == e.official_launcher(
        e._official_image(image))


@pytest.mark.parametrize('fault', ['missing','empty','extra-file','extra-dir',
                                   'case-variant','manifest-absent'])
def test_official_image_rejects_unexpected_inventory(tmp_path,fault):
    parent = tmp_path
    if fault == 'missing':
        image = parent/'image'
    elif fault == 'empty':
        image = parent/'image'; image.mkdir()
    else:
        manifest = valid_manifest()
        if fault == 'case-variant':
            image = parent/'image'; image.mkdir()
            (image/'Claude.exe').write_bytes(OFFICIAL_IMAGE_DATA)
            (image/'image-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        elif fault == 'manifest-absent':
            image = parent/'image'; image.mkdir()
            (image/'claude.exe').write_bytes(OFFICIAL_IMAGE_DATA)
        else:
            image = write_image(parent, 'image', manifest,
                                inventory=('notes.txt',) if fault == 'extra-file' else ())
            if fault == 'extra-dir':
                (image/'subdir').mkdir()
    with pytest.raises(ValueError):
        e._official_image(image)


@pytest.mark.parametrize('fault', ['malformed','duplicate-key','nonfinite','wrong-root',
    'wrong-schema','missing-key','extra-key','wrong-path','wrong-version','digest-uppercase',
    'digest-short','digest-integer','bytes-bool','bytes-zero','bytes-negative','bytes-float',
    'bytes-oversize','nonascii','manifest-oversize'])
def test_official_image_rejects_invalid_manifest(tmp_path,fault):
    manifest = valid_manifest()
    raw = None
    if fault == 'malformed':
        raw = '{ not json'
    elif fault == 'duplicate-key':
        raw = json.dumps(manifest).replace('"path":', '"path":"claude.exe","path":', 1)
    elif fault == 'nonfinite':
        raw = json.dumps(manifest).replace(str(manifest['bytes']), 'NaN', 1)
    elif fault == 'wrong-root':
        raw = '[1,2]'
    elif fault == 'nonascii':
        raw = json.dumps(manifest).replace('2.1.278', '2.1.27\u8e0f', 1)
    elif fault == 'manifest-oversize':
        manifest['padding'] = 'x'*5000
    else:
        manifest = {'wrong-schema': dict(manifest, schema='other'),
                    'missing-key': {k: v for k, v in manifest.items() if k != 'version'},
                    'extra-key': dict(manifest, extra=1),
                    'wrong-path': dict(manifest, path='claude.EXE'),
                    'wrong-version': dict(manifest, version='2.1.277'),
                    'digest-uppercase': dict(manifest, sha256=manifest['sha256'].upper()),
                    'digest-short': dict(manifest, sha256='a'*63),
                    'digest-integer': dict(manifest, sha256=12345),
                    'bytes-bool': dict(manifest, bytes=True),
                    'bytes-zero': dict(manifest, bytes=0),
                    'bytes-negative': dict(manifest, bytes=-1),
                    'bytes-float': dict(manifest, bytes=float(manifest['bytes'])),
                    'bytes-oversize': dict(manifest, bytes=536870913)}[fault]
    image = write_image(tmp_path, 'image', manifest, raw=raw)
    with pytest.raises(ValueError):
        e._official_image(image)


@pytest.mark.parametrize('fault', ['wrong-hash','wrong-size-field','grown-file',
                                   'truncated-file','midread-growth','midread-truncation',
                                   'identity-change'])
def test_official_image_rejects_content_mismatch_or_change(tmp_path,monkeypatch,fault):
    manifest = valid_manifest()
    if fault == 'wrong-hash':
        image = write_image(tmp_path, 'image', dict(manifest, sha256='0'*64))
        expected = 'image_hash_mismatch'
    elif fault == 'wrong-size-field':
        image = write_image(tmp_path, 'image', dict(manifest, bytes=manifest['bytes']+1))
        expected = 'image_size_mismatch'
    elif fault == 'grown-file':
        image = write_image(tmp_path, 'image', manifest)
        with (image/'claude.exe').open('ab') as stream: stream.write(b'grown')
        expected = 'image_size_mismatch'
    elif fault == 'truncated-file':
        image = write_image(tmp_path, 'image', manifest)
        (image/'claude.exe').write_bytes(OFFICIAL_IMAGE_DATA[:100])
        expected = 'image_size_mismatch'
    elif fault in ('midread-growth', 'midread-truncation'):
        path = tmp_path/'large.bin'; path.write_bytes(OFFICIAL_IMAGE_DATA)
        monkeypatch.setattr(e, 'OFFICIAL_IMAGE_CHUNK', 16)
        size = len(OFFICIAL_IMAGE_DATA) + (-10 if fault == 'midread-growth' else 10)
        with pytest.raises(ValueError, match='image_size_mismatch'):
            e._bounded_image_digest(path, size)
        return
    else:
        real = e._identity
        calls = {'count': 0}
        def changing(info):
            calls['count'] += 1
            base = real(info)
            return base if calls['count'] == 1 else (base[0], base[1], base[2], base[3]+1)
        monkeypatch.setattr(e, '_identity', changing)
        image = write_image(tmp_path, 'image', manifest)
        expected = 'image_changed'
    with pytest.raises(ValueError, match=expected):
        e._official_image(image)


def test_official_image_uses_separate_streaming_bound(tmp_path,monkeypatch):
    assert e.MAX_FILE == 150000000 and e.MAX_BYTES == 1500000000
    image = official_image(tmp_path)
    monkeypatch.setattr(e, 'MAX_FILE', 4096)
    value = e._official_image(image)
    assert value['sha256'] == sha256(OFFICIAL_IMAGE_DATA).hexdigest()
    assert value['bytes'] == len(OFFICIAL_IMAGE_DATA) > 4096
    with pytest.raises(ValueError, match='file_too_large'):
        e.file_bytes(image/'claude.exe')
    with pytest.raises(ValueError):
        e.walk(image)
    monkeypatch.setattr(e, 'walk', lambda *a, **k: pytest.fail('payload walker used'))
    calls = []
    real = e.file_bytes
    monkeypatch.setattr(e, 'file_bytes', lambda p: (calls.append(Path(p)), real(p))[1])
    monkeypatch.setattr(e, 'OFFICIAL_IMAGE_CHUNK', 16)
    assert e._official_image(image) == value
    assert all(p.name != 'claude.exe' for p in calls)


@pytest.mark.parametrize('fault', ['missing','empty-file','edited','additional','renamed',
                                   'replaced-by-dir','linked-launcher','linked-control-dir',
                                   'hardlinked-launcher'])
def test_official_control_requires_exact_generated_contents(tmp_path,fault):
    root, image, control = official_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.wsb'
    launcher = control/'official-probe.cmd'
    if fault == 'missing':
        shutil.rmtree(control)
    elif fault == 'empty-file':
        launcher.write_bytes(b'')
    elif fault == 'edited':
        launcher.write_bytes(e.official_launcher(valid_manifest()) + b'rem edited\r\n')
    elif fault == 'additional':
        (control/'extra.cmd').write_bytes(b'x')
    elif fault == 'renamed':
        launcher.rename(control/'other.cmd')
    elif fault == 'replaced-by-dir':
        launcher.unlink(); launcher.mkdir()
    elif fault == 'hardlinked-launcher':
        os.link(launcher, tmp_path/'outside-hard-link')
    else:
        try:
            target = launcher.read_bytes(); launcher.unlink()
            if fault == 'linked-launcher':
                os.symlink(tmp_path/'elsewhere.cmd', launcher)
            else:
                elsewhere = tmp_path/'elsewhere-control'
                shutil.copytree(control, elsewhere)
                launcher.write_bytes(target)
                shutil.rmtree(control)
                os.symlink(elsewhere, control)
        except OSError:
            pytest.skip('symlink permission unavailable on this host')
    before = image_snapshot(image)
    with pytest.raises(ValueError):
        e.official_config(root, image, control, output, destination,
                          isolated_host_attested=True)
    assert not output.exists() and not destination.exists()
    if control.is_dir():
        assert image_snapshot(image) == before
    assert sorted(os.listdir(image)) == ['claude.exe', 'image-manifest.json']


@pytest.mark.parametrize('kind,expected', [('equal','destination_exists'),
    ('nested','mapping_overlap'), ('ancestor','destination_exists'),
    ('case-alias','mapping_overlap'), ('identity-alias','mapping_overlap')])
def test_official_control_rejects_image_overlap_before_creation(tmp_path,monkeypatch,kind,expected):
    image = official_image(tmp_path)
    untouched = image_snapshot(image)
    if kind == 'equal':
        destination = image
    elif kind == 'nested':
        destination = image/'nested-control'
    elif kind == 'ancestor':
        destination = tmp_path
    else:
        destination = tmp_path/'control'
        if kind == 'identity-alias':
            monkeypatch.setattr(e, '_identity', lambda info: ('synthetic', 'alias', 0, 0))
    with pytest.raises(ValueError, match=expected):
        if kind == 'case-alias':
            e._reject_mapping_overlap(Path('C:/Data/Image'), Path('c:\\data\\IMAGE\\nested'))
        else:
            e.official_control(image, destination)
    assert image_snapshot(image) == untouched
    if kind == 'nested':
        assert not destination.exists()
    if kind == 'identity-alias':
        assert not destination.exists()


@pytest.mark.parametrize('kind', ['output-dir','output-file','destination-file',
                                  'destination-dir','destination-broken-link'])
def test_official_config_rejects_existing_targets(tmp_path,kind):
    root, image, control = official_setup(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.wsb'
    if kind == 'output-dir':
        output.mkdir(); (output/'kept').write_bytes(b'marker')
    elif kind == 'output-file':
        output.write_bytes(b'marker')
    elif kind == 'destination-file':
        destination.write_bytes(b'marker')
    elif kind == 'destination-dir':
        destination.mkdir(); (destination/'kept').write_bytes(b'marker')
    else:
        try:
            os.symlink(tmp_path/'nowhere', destination)
        except OSError:
            pytest.skip('symlink permission unavailable on this host')
    with pytest.raises(ValueError):
        e.official_config(root, image, control, output, destination,
                          isolated_host_attested=True)
    if kind == 'output-dir':
        assert (output/'kept').read_bytes() == b'marker'
    if kind == 'destination-file':
        assert destination.read_bytes() == b'marker'
    if kind == 'destination-dir':
        assert (destination/'kept').read_bytes() == b'marker'
    assert not (tmp_path/'official-probe.wsb').is_file() or kind == 'destination-file'


@pytest.mark.parametrize('fault', ['corrupt','missing-entry','extra-entry','layout-missing'])
def test_official_config_payload_verification_failure_creates_nothing(tmp_path,fault):
    parent = tmp_path/'nested'; parent.mkdir()
    if fault == 'layout-missing':
        root, _ = official_payload(parent, complete=False)
    else:
        root, _ = official_payload(parent)
        if fault == 'corrupt':
            (root/'smoke.cmd').write_bytes(b'changed')
        elif fault == 'missing-entry':
            (root/'source/synthetic.py').unlink()
        elif fault == 'extra-entry':
            (root/'unexpected.txt').write_bytes(b'x')
    image = official_image(parent); control = parent/'control'
    e.official_control(image, control)
    output = parent/'official-output'; destination = parent/'official-probe.wsb'
    with pytest.raises(ValueError):
        e.official_config(root, image, control, output, destination,
                          isolated_host_attested=True)
    assert not output.exists() and not destination.exists()
    assert (control/'official-probe.cmd').is_file()


def test_official_paths_fail_closed(tmp_path):
    hostile = (r'\\server\share\image', r'\\?\C:\x', r'\\.\C:\x', r'\\.\PhysicalDisk0',
        'C:image', 'C:', 'image', r'\rooted', '/abs', 'C::x', r'C:\a\..\b', r'C:\..\b',
        r'C:\a\.\b', r'C:\a\file:ads', r'C:\a\f:s:$DATA', r'C:\a\CON', r'C:\a\con.txt',
        r'C:\a\COM1.log', r'C:\a\nul.exe', r'C:\a\LPT9', r'C:\a\name.', r'C:\a\name ',
        r'C:\a\na<me', r'C:\a\na>me', r'C:\a\na|me', r'C:\a\na?me', r'C:\a\na*me',
        r'C:\a\na"me', r'C:\%TEMP%\x', r'C:\a%b', 'C:\\a\x00b', 'C:\\a\rb',
        'C:\\a\x7fb', '', 'x'*5000)
    for text in hostile:
        assert e._windows_path_problem(text) is not None, text
    accepted = (r'C:\pal', r'C:\PAL-INPUT\stage 1\input', 'C:/data/x', r'C:\a\b.c~1',
                r'D:\deep\nest\ed', 'C:\\')
    for text in accepted:
        assert e._windows_path_problem(text) is None, text
    class _ReparseDir:
        def lstat(self):
            return types.SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
    with pytest.raises(ValueError, match='nonplain_path'):
        e.plain(_ReparseDir())
    image = official_image(tmp_path)
    (tmp_path/'afile').write_bytes(b'plain file parent')
    with pytest.raises(ValueError):
        e.official_control(image, tmp_path/'afile'/'control')
    assert not (tmp_path/'afile'/'control').exists()
    with pytest.raises(ValueError, match='official_path_invalid'):
        e.official_control(image, tmp_path/'a%b')
    with pytest.raises(ValueError, match='official_path_invalid'):
        e.official_control(image, tmp_path/'a'/'..'/'b')
    assert not (tmp_path/'a%b').exists() and not (tmp_path/'b').exists()
    linked = False
    try:
        (tmp_path/'realparent').mkdir()
        os.symlink(tmp_path/'realparent', tmp_path/'linkparent')
        linked = True
    except OSError:
        linked = False
    if linked:
        with pytest.raises(ValueError):
            e.official_control(image, tmp_path/'linkparent'/'control')
        assert not (tmp_path/'linkparent'/'control').exists()


def test_official_paths_reject_identity_alias_overlap(tmp_path,monkeypatch):
    image = official_image(tmp_path)
    destination = tmp_path/'control'
    monkeypatch.setattr(e, '_identity', lambda info: ('synthetic-host', 'shared', 0, 0))
    with pytest.raises(ValueError, match='mapping_overlap'):
        e.official_control(image, destination)
    assert not destination.exists()
    assert sorted(os.listdir(image)) == ['claude.exe', 'image-manifest.json']
    monkeypatch.undo()
    short = None
    if sys.platform == 'win32':
        import ctypes
        buffer = ctypes.create_unicode_buffer(1024)
        count = ctypes.windll.kernel32.GetShortPathNameW(str(tmp_path), buffer, 1024)
        candidate = buffer.value if 0 < count < 1024 else ''
        if candidate and candidate.lower() != str(tmp_path).lower():
            short = candidate
    if short:
        alias_image = official_image(tmp_path, 'aliased-image')
        assert Path(short).is_dir()
        with pytest.raises(ValueError, match='mapping_overlap'):
            e.official_control(alias_image, Path(short)/'aliased-image'/'nested')
        assert not (alias_image/'nested').exists()
    else:
        print('Windows 8.3 short-name alias unavailable on this host; skipped physical alias')


def test_official_cli_argument_validation(tmp_path,monkeypatch,capsys):
    image = official_image(tmp_path)
    def cli(*args):
        monkeypatch.setattr(sys, 'argv', ['probe', *args])
        return e.main()
    with pytest.raises(SystemExit) as missing:
        cli('official-control', '--image-dir', str(image))
    assert missing.value.code == 2
    for refused in (['--image', str(image)], ['--image-dir', str(image), '--nope', 'v'],
                    ['--imag-dir', str(image), '--destination', str(tmp_path/'c')],
                    ['--image', str(image), '--destination', str(tmp_path/'c')]):
        with pytest.raises(SystemExit) as exit_code:
            cli('official-control', *refused)
        assert exit_code.value.code == 2
    assert not (tmp_path/'c').exists()
    assert cli('official-control', '--image-dir', str(image),
               '--destination', str(tmp_path/'control')) == 0
    status = json.loads(capsys.readouterr().out)
    assert status['status'] == 'official_control_generated_not_launched'
    assert status['official_cli_executed'] is False and status['activation_authorized'] is False
    root, _ = official_payload(tmp_path)
    output = tmp_path/'official-output'; destination = tmp_path/'official-probe.wsb'
    base = ['official-config', '--payload-root', str(root), '--image-dir', str(image),
            '--control-dir', str(tmp_path/'control'), '--output-dir', str(output),
            '--destination', str(destination)]
    assert cli(*base) == 1
    refusal = json.loads(capsys.readouterr().out)
    assert refusal['status'] == 'BLOCKED'
    assert refusal['reason'] == 'isolated_host_attestation_required'
    assert not output.exists() and not destination.exists()
    assert cli(*base[:-2], '--destination', str(tmp_path/'official-probe.txt'),
               '--isolated-host-attested') == 1
    suffix = json.loads(capsys.readouterr().out)
    assert suffix['reason'] == 'destination_suffix_invalid'
    assert not output.exists() and not (tmp_path/'official-probe.txt').exists()
    assert cli(*base, '--isolated-host-attested') == 0
    final = json.loads(capsys.readouterr().out)
    assert final['status'] == 'official_config_generated_not_launched'
    assert final['official_cli_executed'] is False and final['activation_authorized'] is False
    assert list(output.iterdir()) == [] and destination.is_file()


def test_official_partial_io_failure_preserves_attempt(tmp_path,monkeypatch):
    image = official_image(tmp_path)
    control = tmp_path/'control'
    real = e._exclusive_write
    monkeypatch.setattr(e, '_exclusive_write',
                        lambda p, d: (_ for _ in ()).throw(OSError('synthetic control write failure'))
                        if p == control/'official-probe.cmd' else real(p, d))
    with pytest.raises(OSError):
        e.official_control(image, control)
    assert control.is_dir() and list(control.iterdir()) == []
    with pytest.raises(ValueError, match='destination_exists'):
        e.official_control(image, control)
    assert control.is_dir()
    monkeypatch.undo()
    shutil.rmtree(control)
    e.official_control(image, control)
    root, _ = official_payload(tmp_path)
    output = tmp_path/'official-output'; config = tmp_path/'official-probe.wsb'
    monkeypatch.setattr(e, '_exclusive_write',
                        lambda p, d: (_ for _ in ()).throw(OSError('synthetic config write failure'))
                        if p == config else real(p, d))
    with pytest.raises(OSError):
        e.official_config(root, image, control, output, config, isolated_host_attested=True)
    assert output.is_dir() and list(output.iterdir()) == []
    assert not config.exists()
    with pytest.raises(ValueError, match='output_dir_exists'):
        e.official_config(root, image, control, output, config, isolated_host_attested=True)
    assert output.is_dir() and not config.exists()


def test_legacy_preparation_bytes_and_modes_unchanged(tmp_path,monkeypatch,capsys):
    assert e.SMOKE_CMD == (b'@echo off\r\nC:\\pal-input\\python\\python.exe -I -S -B '
        b'C:\\pal-input\\probe-environment.py selftest --root C:\\pal-input '
        b'--receipt C:\\pal-output\\environment.json\r\n')
    xml = e.sandbox_xml(Path('C:/x/input'), Path('C:/x/output'))
    assert xml.startswith(b"<?xml version='1.0' encoding='utf-8'?>")
    doc = ET.fromstring(xml)
    for tag in ('Networking','ClipboardRedirection','vGPU','AudioInput','VideoInput',
                'PrinterRedirection'):
        assert doc.findtext(tag) == 'Disable'
    assert doc.findtext('ProtectedClient') == 'Enable'
    assert doc.findtext('MemoryInMB') == '4096'
    assert [(m.findtext('HostFolder'),m.findtext('SandboxFolder'),m.findtext('ReadOnly'))
            for m in doc.findall('MappedFolders/MappedFolder')] == [
        (str(Path('C:/x/input')), r'C:\pal-input', 'true'),
        (str(Path('C:/x/output')), r'C:\pal-output', 'false')]
    assert doc.findtext('LogonCommand/Command') == (
        r'C:\Windows\System32\cmd.exe /d /c C:\pal-input\smoke.cmd')
    staged = tmp_path/'staged'; staged.mkdir()
    z, h = archive(staged)
    result = e.stage(z, h, tmp_path/'new-stage')
    assert result == dict(status='staged_not_launched', source_commit='a'*40,
                          official_cli_included=False, activation_authorized=False)
    assert (tmp_path/'new-stage'/'preparation-smoke.wsb').is_file()
    direct = tmp_path/'direct'; direct.mkdir()
    root, m = payload(direct)
    assert e.verify(root) == m
    monkeypatch.setattr(sys, 'argv', ['probe', 'verify', '--root', str(root)])
    assert e.main() == 0
    assert json.loads(capsys.readouterr().out) == dict(
        status='verified_not_activated', source_commit='a'*40)
    with pytest.raises(ValueError, match='ci_build_only'):
        e.build(tmp_path, tmp_path/'build-out', True)
    assert not (tmp_path/'build-out').exists()
    with pytest.raises(ValueError, match='runtime_platform_mismatch|runtime_origin_mismatch'):
        e.selftest(root, tmp_path/'receipt.json')
    assert not (tmp_path/'receipt.json').exists()
