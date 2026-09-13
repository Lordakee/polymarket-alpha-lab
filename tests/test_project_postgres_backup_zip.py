"""Zip central-directory bounds must apply BEFORE ZipFile allocates its index."""
from io import BytesIO
import struct
import zipfile

import pytest

from polymarket_alpha_lab.project_postgres import backup_format as fmt
from polymarket_alpha_lab.project_postgres.backup_zip import validate_zip_layout
from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError


def sample():
    stream=BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('data/item',b'fixture')
    return stream.getvalue()


def test_normal_archive_and_small_zip64_layout():
    raw=sample();validate_zip_layout(BytesIO(raw))
    sig,disk,cd_disk,here,total,size,offset,comment=struct.unpack('<4s4H2IH',raw[-22:])
    extended=(raw[:-22]+struct.pack('<4sQ2H2I4Q',b'PK\x06\x06',44,45,45,0,0,here,total,size,offset)
              +struct.pack('<4sIQI',b'PK\x06\x07',0,len(raw)-22,1)
              +struct.pack('<4s4H2IH',sig,0,0,here,total,0xffffffff,0xffffffff,0))
    validate_zip_layout(BytesIO(extended))
    with zipfile.ZipFile(BytesIO(extended)) as z:assert z.read('data/item')==b'fixture'


@pytest.mark.parametrize('field,value',[(1,1),(2,1),(3,0),(4,0),(4,50002),(5,0x7fffffff),(6,1),(7,1)])
def test_invalid_end_record_is_bounded(field,value):
    raw=sample();fields=list(struct.unpack('<4s4H2IH',raw[-22:]));fields[field]=value
    bad=raw[:-22]+struct.pack('<4s4H2IH',*fields)
    with pytest.raises(ProjectDatabaseError):validate_zip_layout(BytesIO(bad))


def test_directory_limit_is_checked_before_reading_directory(monkeypatch):
    raw=sample()
    class Guard(BytesIO):
        def read(self,n=-1):
            assert n <= 56, 'must reject before reading the central directory'
            return super().read(n)
    monkeypatch.setattr(fmt,'MAX_MANIFEST_BYTES',1)
    with pytest.raises(ProjectDatabaseError):validate_zip_layout(Guard(raw))


def test_misreported_entry_count_does_not_allocate_extra_members():
    raw=sample();fields=list(struct.unpack('<4s4H2IH',raw[-22:]));fields[3]=fields[4]=2
    with pytest.raises(ProjectDatabaseError):validate_zip_layout(BytesIO(raw[:-22]+struct.pack('<4s4H2IH',*fields)))


@pytest.mark.parametrize('bad',[b'',b'PK\x05\x06',b'X'*22])
def test_truncated_or_nonzip_input(bad):
    with pytest.raises(ProjectDatabaseError):validate_zip_layout(BytesIO(bad))


from tests.test_project_postgres_backup import state, make
from polymarket_alpha_lab.project_postgres import backup
from hashlib import sha256


def test_public_verifier_rejects_misreported_directory_count(state):
    root, layout, data, destination = state
    path, _ = make(state)
    raw = path.read_bytes()
    fields = list(struct.unpack('<4s4H2IH', raw[-22:]))
    fields[3] += 1
    fields[4] += 1
    changed = raw[:-22] + struct.pack('<4s4H2IH', *fields)
    path.write_bytes(changed)
    with pytest.raises(ProjectDatabaseError, match='backup_invalid'):
        backup.verify_cold_backup(root, archive=path,
            expected_sha256=sha256(changed).hexdigest(), trusted_backup=True)
