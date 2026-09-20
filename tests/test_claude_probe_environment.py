"""Preparation package refusal tests; no real CLI, global install, or VM launch."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
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
    assert doc.findtext('MappedFolders/MappedFolder/HostFolder')=='C:/clean & dedicated/input'
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
