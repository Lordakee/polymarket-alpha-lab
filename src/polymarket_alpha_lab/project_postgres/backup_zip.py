"""Pre-allocation ZIP/ZIP64 framing checks for this project's closed backup format.

Our writer produces single-disk, no-comment archives. Bound directory bytes and
count its fixed headers BEFORE constructing ZipFile, which eagerly builds an
index. No private zipfile APIs or unbounded directory allocations are used here.
"""
import os
import struct

from . import backup_format as fmt


def validate_zip_layout(raw) -> None:
    raw.seek(0, os.SEEK_END)
    length = raw.tell()
    if not 22 <= length <= fmt.MAX_BYTES + fmt.MAX_MANIFEST_BYTES:
        fmt.invalid()
    raw.seek(length - 22)
    end = raw.read(22)
    signature, disk, cd_disk, here, count, size, offset, comment = struct.unpack('<4s4H2IH', end)
    if signature != b'PK\x05\x06' or disk or cd_disk or comment or here != count:
        fmt.invalid()
    boundary = length - 22
    if count == 0xffff or size == 0xffffffff or offset == 0xffffffff:
        if length < 98:
            fmt.invalid()
        raw.seek(length - 42)
        locator, disk, position, disks = struct.unpack('<4sIQI', raw.read(20))
        if locator != b'PK\x06\x07' or disk or disks != 1 or position + 56 != length - 42:
            fmt.invalid()
        raw.seek(position)
        signature, record_size, made, needed, disk, cd_disk, here, count, size, offset = struct.unpack('<4sQ2H2I4Q', raw.read(56))
        if signature != b'PK\x06\x06' or record_size != 44 or disk or cd_disk or here != count or needed != 45:
            fmt.invalid()
        boundary = position
    if (not 1 <= count <= fmt.MAX_ENTRIES + 1 or size > fmt.MAX_MANIFEST_BYTES
            or offset + size != boundary):
        fmt.invalid()
    raw.seek(offset)
    directory = raw.read(size)
    if len(directory) != size:
        fmt.invalid()
    index = actual = 0
    while index < size:
        if size - index < 46 or directory[index:index + 4] != b'PK\x01\x02':
            fmt.invalid()
        name, extra, comment = struct.unpack_from('<3H', directory, index + 28)
        if not 1 <= name <= 401 or comment:
            fmt.invalid()
        index += 46 + name + extra + comment
        actual += 1
        if actual > count or index > size:
            fmt.invalid()
    if actual != count:
        fmt.invalid()
    raw.seek(0)
