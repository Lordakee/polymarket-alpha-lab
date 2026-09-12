"""Private installation paths and cross-process lifecycle ownership."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import file_digest, sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import tomllib


class ProjectDatabaseError(RuntimeError):
    """Only fixed public error codes; never provider output or credentials."""


def fail(code: str):
    raise ProjectDatabaseError(code) from None


def no_links(path: Path) -> None:
    """Reject symlinks and Windows reparse points, including existing ancestors."""
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            fail('project_postgres_link_rejected')


def clean_environment() -> dict[str, str]:
    # PostgreSQL settings and dynamic-loader overrides must not select another
    # server/library/config. Model-provider variables are not inspected here.
    excluded = {'PYTHONPATH', 'PYTHONHOME', 'LD_PRELOAD', 'LD_LIBRARY_PATH',
                'DYLD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES'}
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')
           and k.upper() not in excluded}
    env.update(LC_ALL='C', LANG='C', TZ='UTC')
    return env


def command(args: list[str], *, env=None, stdin: str | None = None,
            timeout: int = 60, accepted: tuple[int, ...] = (0,),
            capture_output: bool = True, cwd: str | None = None) -> subprocess.CompletedProcess:
    # Server launchers may leave descendants alive after they exit. Inherited
    # PIPE handles can prevent Windows communicate() (including its timeout
    # cleanup) from returning. Such commands need DEVNULL, not captured pipes.
    streams = ({'capture_output': True} if capture_output else
               {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL})
    if stdin is None:
        streams['stdin'] = subprocess.DEVNULL
    try:
        result = subprocess.run(args, input=stdin, env=clean_environment() if env is None else env,
            **streams, text=True, encoding='utf-8', errors='strict',
            timeout=timeout, check=False, shell=False, cwd=cwd)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        fail('project_postgres_command_failed')
    if result.returncode not in accepted:
        fail('project_postgres_command_failed')
    return result


def _windows_acl(path: Path, *, create: bool) -> None:
    # Use the OS's absolute PowerShell path, not PATH lookup or shell quoting.
    # Only an infrastructure pathname travels in the child environment.
    exe = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    script = r'''
$ErrorActionPreference='Stop'
$stage=10
try {
  $p=$env:PAL_PRIVATE_DIRECTORY
  $sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
  if ($env:PAL_CREATE_ACL -eq '1') {
    $stage=11
    $a=[System.Security.AccessControl.DirectorySecurity]::new()
    $a.SetOwner($sid)
    $a.SetAccessRuleProtection($true,$false)
    $inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
    foreach ($value in @($sid.Value,'S-1-5-18')) {
      $id=[System.Security.Principal.SecurityIdentifier]::new($value)
      $r=[System.Security.AccessControl.FileSystemAccessRule]::new($id,[System.Security.AccessControl.FileSystemRights]::FullControl,$inherit,[System.Security.AccessControl.PropagationFlags]::None,[System.Security.AccessControl.AccessControlType]::Allow)
      $a.AddAccessRule($r)
    }
    $stage=12
    [System.IO.Directory]::SetAccessControl($p,$a)
  }
  $stage=13
  $a=[System.IO.Directory]::GetAccessControl($p,[System.Security.AccessControl.AccessControlSections]::Access -bor [System.Security.AccessControl.AccessControlSections]::Owner)
  if (-not $a.AreAccessRulesProtected) {exit 14}
  if ($a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne $sid.Value) {exit 15}
  $allowed=@($sid.Value,'S-1-5-18')
  $ownerAllowed=$false
  foreach ($r in $a.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])) {
    if ($r.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Allow) {
      if ($allowed -notcontains $r.IdentityReference.Value) {exit 16}
      if ($r.IdentityReference.Value -eq $sid.Value -and ($r.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -eq [System.Security.AccessControl.FileSystemRights]::FullControl) {$ownerAllowed=$true}
    }
  }
  if (-not $ownerAllowed) {exit 17}
  exit 0
} catch {exit $stage}
'''
    env = clean_environment()
    env.update(PAL_PRIVATE_DIRECTORY=str(path), PAL_CREATE_ACL='1' if create else '0')
    try:
        result = command([str(exe), '-NoProfile', '-NonInteractive', '-Command', script],
                         env=env, accepted=(0, *range(10, 18)))
    except ProjectDatabaseError:
        fail('project_postgres_private_permissions_required')
    if result.returncode:
        # Fixed stage codes distinguish construction/application/verification
        # failures without publishing paths, ACL principals or child stderr.
        fail('project_postgres_private_permissions_required_' + str(result.returncode))


def private_directory(path: Path, *, create: bool = False) -> None:
    no_links(path)
    if create:
        path.mkdir(mode=0o700, parents=False, exist_ok=False)
    if not path.is_dir():
        fail('project_postgres_private_directory_missing')
    if os.name == 'nt':
        _windows_acl(path, create=create)
    else:
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            fail('project_postgres_private_permissions_required')


def write_private(path: Path, contents: str | bytes) -> None:
    """Create-only infrastructure file. Never overwrite an existing file."""
    no_links(path)
    raw = contents.encode('utf-8') if type(contents) is str else contents
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def read_private(path: Path, *, limit: int = 1048576) -> str:
    no_links(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        fail('project_postgres_invalid_private_file')
    if os.name != 'nt' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        fail('project_postgres_private_permissions_required')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        fail('project_postgres_invalid_private_file')
    return raw.decode('utf-8')


def digest_file(path: Path) -> str:
    no_links(path)
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


@dataclass(frozen=True)
class Layout:
    root: Path

    def __post_init__(self):
        root = Path(self.root).absolute()
        if any(ord(c) < 32 or c in "\"'&|<>^%" for c in str(root)):
            fail('project_postgres_unsupported_project_path')
        no_links(root)
        root = root.resolve()
        try:
            with (root / 'pyproject.toml').open('rb') as stream:
                name = tomllib.load(stream)['project']['name']
            if name != 'polymarket-alpha-lab':
                raise ValueError
            if not (root / 'database/migrations.lock.json').is_file():
                raise ValueError
        except (OSError, ValueError, KeyError):
            fail('project_postgres_project_root_required')
        object.__setattr__(self, 'root', root)

    @property
    def private(self):
        return self.root / '.local'

    @property
    def home(self):
        return self.private / 'postgres'

    @property
    def runtime(self):
        return self.root / 'runtime' / 'postgres'

    @property
    def cluster(self):
        return self.home / 'data'

    @property
    def root_hash(self):
        return sha256(os.path.normcase(str(self.root)).encode('utf-8')).hexdigest()

    def prepare_private(self):
        private_directory(self.private, create=not self.private.exists())

    @contextmanager
    def lock(self):
        """Exclusive owner across init/up/down/migrate AND application session.

        The OS releases ownership after a crash; we never delete another
        process's lock file or trust a stale PID as ownership.
        """
        self.prepare_private()
        path = self.private / 'postgres.lock'
        no_links(path)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        locked = False
        try:
            if os.fstat(fd).st_size == 0:
                os.write(fd, b'\0')
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                fail('project_postgres_busy')
            yield
        finally:
            if locked:
                os.lseek(fd, 0, os.SEEK_SET)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
