"""Actual PowerShell parser/filesystem tests; HTTP is replaced with fixture bytes."""
from base64 import b64encode
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

import pytest

from tests.handoff_process_probe import POWERSHELL_PROBE, run_fixture

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/download_handoff.ps1'


def test_bootstrap_is_ascii_and_never_automatically_executes_downloads():
    source = SCRIPT.read_bytes()
    source.decode('ascii')
    assert b'Invoke-Expression' not in source and b'ExecutionPolicy' not in source
    assert b'AllowAutoRedirect = $false' in source and b'UseDefaultCredentials = $false' in source
    assert b'FileMode]::CreateNew' in source and b'Directory]::Move' in source
    assert b'Remove-Item' not in source and b'git apply' not in source


def encoded(value):
    return b64encode(str(value).encode('utf-8')).decode()


@pytest.mark.parametrize('shell', ['powershell.exe', 'pwsh'])
@pytest.mark.parametrize('case', ['success', 'manifest_hash', 'file_hash', 'partial', 'path', 'duplicate', 'oversize', 'false_size'])
def test_real_powershell_download_publication(tmp_path, shell, case, record_property):
    program = shutil.which(shell)
    if os.name == 'nt' and not program and os.environ.get('PAL_REQUIRE_HANDOFF_SHELLS') == '1':
        pytest.fail('required Windows handoff shell is missing')
    if not program or os.name != 'nt':
        pytest.skip('real Windows PowerShell 5.1 / PowerShell 7 integration')
    parent=tmp_path/'Download space \u6d4b\u8bd5'
    parent.mkdir()
    (parent/'protected.txt').write_bytes(b'previous evidence')
    payload=b'# synthetic fixture only\n'
    entry=dict(name='LOCAL_AGENT_PROMPT.md',bytes=len(payload),sha256=sha256(payload).hexdigest())
    manifest=dict(format='github-handoff-v2', files=[entry])
    if case=='path':entry['name']='../escape.ps1'
    if case=='duplicate':manifest['files'].append(dict(entry))
    if case=='oversize':entry['bytes']=1048577
    if case=='false_size':entry['bytes']=True
    mbytes=json.dumps(manifest).encode()
    expected='0'*64 if case=='manifest_hash' else sha256(mbytes).hexdigest()
    fixtures=tmp_path/'fixtures';fixtures.mkdir()
    (fixtures/'manifest.json').write_bytes(mbytes)
    (fixtures/'LOCAL_AGENT_PROMPT.md').write_bytes(payload if case!='file_hash' else b'x'*len(payload))
    harness = POWERSHELL_PROBE + f'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Write-HandoffProbe 'encoding_ready'
function Decode([string]$x) {{ [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($x)) }}
. (Decode '{encoded(SCRIPT)}')
Write-HandoffProbe 'helper_loaded'
$Global:Source = Decode '{encoded(fixtures)}'
$Global:Case = '{case}'
$Global:Calls = 0
function Get-FileHash {{ throw 'Get-FileHash must not be required' }}
function Receive-HandoffFile {{
    param([string]$Uri, [string]$Destination, [long]$Limit)
    $Global:Calls++
    $Name = ([uri]$Uri).Segments[-1]
    if ($Name -eq 'manifest.json') {{ Write-HandoffProbe 'manifest_entered' }}
    else {{ Write-HandoffProbe 'payload_entered' }}
    $Bytes = [IO.File]::ReadAllBytes((Join-Path $Global:Source $Name))
    if ($Global:Case -eq 'partial' -and $Name -ne 'manifest.json') {{
        [IO.File]::WriteAllBytes($Destination, $Bytes[0..3])
        Write-HandoffProbe 'partial_expected'
        throw 'injected incomplete transfer'
    }}
    [IO.File]::WriteAllBytes($Destination, $Bytes)
    if ($Name -eq 'manifest.json') {{ Write-HandoffProbe 'manifest_returned' }}
    else {{ Write-HandoffProbe 'payload_returned' }}
}}
Write-HandoffProbe 'invoke_entered'
$Result = Invoke-HandoffDownload 'wmqfl861/polymarket-alpha-lab' ('a'*40) 'handoffs/unit-test' '{expected}' (Decode '{encoded(parent)}')
Write-HandoffProbe 'invoke_returned'
Write-HandoffProbe 'serialization_entered'
[pscustomobject]@{{result=$Result; calls=$Global:Calls; major=$PSVersionTable.PSVersion.Major}} | ConvertTo-Json -Depth 8 -Compress
Write-HandoffProbe 'serialization_returned'
'''
    ps=tmp_path/'test.ps1';ps.write_bytes(harness.encode('ascii'))
    run, trace = run_fixture(program, ps, record_property=record_property)
    assert run.returncode==0, run.stdout+run.stderr
    stages = [entry['stage'] for entry in trace['stages']]
    transfers = ['manifest_entered', 'manifest_returned']
    if case in ('success', 'file_hash', 'partial'):
        transfers += ['payload_entered', 'partial_expected' if case == 'partial' else 'payload_returned']
    assert stages == ['script_entered', 'encoding_ready', 'helper_loaded', 'invoke_entered',
                      *transfers, 'invoke_returned', 'serialization_entered', 'serialization_returned']
    assert not trace['malformed_marker_seen'] and not trace['trace_truncated']
    result=json.loads(run.stdout.strip())
    assert result['major']==(5 if shell=='powershell.exe' else 7)
    assert result['result']['executed'] is False
    assert (parent/'protected.txt').read_bytes()==b'previous evidence'
    published=list(parent.glob('pal-handoff-*'))
    staging=list(parent.glob('.pal-handoff-*.downloading'))
    if case=='success':
        assert result['result']['status']=='verified' and result['calls']==2, result
        assert len(published)==1 and not staging
        assert Path(result['result']['directory']) == published[0]
        assert (published[0]/'LOCAL_AGENT_PROMPT.md').read_bytes()==payload
        assert (published[0]/'manifest.json').read_bytes()==mbytes
    else:
        assert result['result']['status']=='failed' and len(staging)==1 and not published
        assert result['calls']==(2 if case in ('file_hash','partial') else 1)
        assert not (tmp_path/'escape.ps1').exists()
        if case=='partial':
            assert (staging[0]/'LOCAL_AGENT_PROMPT.md.part').read_bytes()==payload[:4]


@pytest.mark.parametrize('shell', ['powershell.exe', 'pwsh'])
def test_dotnet_hash_is_exact_unicode_safe_and_releases_file(tmp_path, shell, record_property):
    program = shutil.which(shell)
    if os.name == 'nt' and not program and os.environ.get('PAL_REQUIRE_HANDOFF_SHELLS') == '1':
        pytest.fail('required Windows handoff shell is missing')
    if not program or os.name != 'nt':
        pytest.skip('real Windows PowerShell 5.1 / PowerShell 7 integration')
    payload = b'\x00\xff\x80' + 'fixture \u6d4b\u8bd5'.encode('utf-8')
    item = tmp_path / 'hash \u6d4b\u8bd5.bin'
    item.write_bytes(payload)
    ps = tmp_path / 'hash.ps1'
    ps.write_text(POWERSHELL_PROBE + f"""
$ErrorActionPreference = 'Stop'
function Decode([string]$x) {{ [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($x)) }}
. (Decode '{encoded(SCRIPT)}')
Write-HandoffProbe 'helper_loaded'
function Get-FileHash {{ throw 'Get-FileHash must not be required' }}
$Path = Decode '{encoded(item)}'
Write-HandoffProbe 'hash_entered'
$Hash = Get-HandoffSha256 $Path
Write-HandoffProbe 'hash_returned'
$Check = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
$Check.Dispose()
Write-HandoffProbe 'serialization_entered'
[pscustomobject]@{{sha256=$Hash; major=$PSVersionTable.PSVersion.Major}} | ConvertTo-Json -Compress
Write-HandoffProbe 'serialization_returned'
""", encoding='ascii')
    run, trace = run_fixture(program, ps, record_property=record_property)
    assert run.returncode == 0, run.stdout + run.stderr
    assert [entry['stage'] for entry in trace['stages']] == [
        'script_entered', 'helper_loaded', 'hash_entered', 'hash_returned',
        'serialization_entered', 'serialization_returned']
    assert not trace['malformed_marker_seen'] and not trace['trace_truncated']
    value = json.loads(run.stdout)
    assert value['sha256'] == sha256(payload).hexdigest()
    assert value['major'] == (5 if shell == 'powershell.exe' else 7)
    assert item.read_bytes() == payload
