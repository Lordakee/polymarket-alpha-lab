"""Actual PowerShell parser/filesystem tests; HTTP is replaced with fixture bytes."""
from base64 import b64encode
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

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
def test_real_powershell_download_publication(tmp_path, shell, case):
    program = shutil.which(shell)
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
    harness = f'''
$ErrorActionPreference = 'Stop'
function Decode([string]$x) {{ [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($x)) }}
. (Decode '{encoded(SCRIPT)}')
$Global:Source = Decode '{encoded(fixtures)}'
$Global:Case = '{case}'
$Global:Calls = 0
function Receive-HandoffFile {{
    param([string]$Uri, [string]$Destination, [long]$Limit)
    $Global:Calls++
    $Name = ([uri]$Uri).Segments[-1]
    $Bytes = [IO.File]::ReadAllBytes((Join-Path $Global:Source $Name))
    if ($Global:Case -eq 'partial' -and $Name -ne 'manifest.json') {{
        [IO.File]::WriteAllBytes($Destination, $Bytes[0..3])
        throw 'injected incomplete transfer'
    }}
    [IO.File]::WriteAllBytes($Destination, $Bytes)
}}
$Result = Invoke-HandoffDownload 'wmqfl861/polymarket-alpha-lab' ('a'*40) 'handoffs/unit-test' '{expected}' (Decode '{encoded(parent)}')
[pscustomobject]@{{result=$Result; calls=$Global:Calls; major=$PSVersionTable.PSVersion.Major}} | ConvertTo-Json -Depth 8 -Compress
'''
    ps=tmp_path/'test.ps1';ps.write_bytes(harness.encode('ascii'))
    run=subprocess.run([program,'-NoProfile','-NonInteractive','-File',str(ps)],capture_output=True,
                       text=True,encoding='utf-8',errors='replace',timeout=30)
    assert run.returncode==0, run.stdout+run.stderr
    result=json.loads(run.stdout.strip())
    assert result['major']==(5 if shell=='powershell.exe' else 7)
    assert result['result']['executed'] is False
    assert (parent/'protected.txt').read_bytes()==b'previous evidence'
    published=list(parent.glob('pal-handoff-*'))
    staging=list(parent.glob('.pal-handoff-*.downloading'))
    if case=='success':
        assert result['result']['status']=='verified' and result['calls']==2
        assert len(published)==1 and not staging
        assert (published[0]/'LOCAL_AGENT_PROMPT.md').read_bytes()==payload
        assert (published[0]/'manifest.json').read_bytes()==mbytes
    else:
        assert result['result']['status']=='failed' and len(staging)==1 and not published
        assert result['calls']==(2 if case in ('file_hash','partial') else 1)
        assert not (tmp_path/'escape.ps1').exists()
        if case=='partial':
            assert (staging[0]/'LOCAL_AGENT_PROMPT.md.part').read_bytes()==payload[:4]
