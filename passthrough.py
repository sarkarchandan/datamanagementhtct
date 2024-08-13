"""
passthrough.py
==============
Demonstrates a transparent virtual file system implementation is user space, where all file I/O
operations are delegated to the os module operations to be converted as system calls. It is a
process like any other. That means, the virtual mount point remains active, while the process is
running.

NOTE: With the current version of the fusepy package we can only use a directory inside the /home
as the desired mount point. This behavior is verified with WSL2 on Windows. It needs to be tested
in Linux environment.
"""
import os
import errno
import sys
from typing import Any, Dict, Generator, Optional, Tuple, Union
import fuse


class PassThrough(fuse.Operations):
    """
    Implements a passthrough file system mount where all file operations are delegated to the os
    module operations to be converted as system calls.
    """

    root: str

    def __init__(self, root: str) -> None:
        self.root = root

    # Helpers
    # =======
    def _full_path(self, partial: str) -> str:
        if partial.startswith("/"):
            partial = partial[1:]
        return os.path.join(self.root, partial)

    # FileSystem Methods
    # ==================
    def access(self, path: str, mode: int) -> None:
        if not os.access(self._full_path(path), mode):
            raise fuse.FuseOSError(errno.EACCES)

    def chmod(self, path: str, mode: int) -> None:
        os.chmod(self._full_path(path), mode)

    def chown(self, path: str, uid: int, gid: int) -> None:
        os.chown(self._full_path(path), uid, gid)

    def getattr(self, path: str, fd: Optional[int] = None) -> Dict[str, Any]:
        stat = os.lstat(self._full_path(path))
        return dict((key, getattr(stat, key)) for key in (
            "st_atime", "st_ctime", "st_mtime", "st_uid", "st_gid", "st_mode", "st_nlink",
            "st_size"))

    def readdir(self, path: str, fd: Optional[int] = None) -> Generator[str, None, None]:
        items = [".", ".."]
        if os.path.isdir(self._full_path(path)):
            items.extend(os.listdir(self._full_path(path)))
        for item in items:
            yield item

    def readlink(self, path: str) -> str:
        path_name: str = os.readlink(self._full_path(path))
        if path_name.startswith("/"):
            return os.path.relpath(path_name, self.root)
        else:
            return path_name

    def mknod(self, path: str, mode: int, device: int) -> None:
        os.mknod(self._full_path(path), node, device)

    def rmdir(self, path: str) -> None:
        os.rmdir(self._full_path(path))

    def mkdir(self, path: str, mode: int) -> None:
        os.mkdir(self._full_path(path), mode)

    def statfs(self, path: str) -> Dict[str, Any]:
        stv = os.statvfs(self._full_path(path))
        return dict((key, getattr(stv, key)) for key in (
            "f_bavail", "f_bfree", "f_blocks", "f_bsize", "f_favail", "f_ffree", "f_files",
            "f_flag", "f_frsize", "f_namemax"))

    def unlink(self, path: str) -> None:
        os.unlink(self._full_path(path))

    def symlink(self, name: str, target: str) -> None:
        os.symlink(name, self._full_path(target))

    def rename(self, old: str, new: str) -> None:
        os.rename(self._full_path(old), self._full_path(new))

    def link(self, target: str, name: str) -> None:
        os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path: str, times: Optional[Union[Tuple[int, int], Tuple[float, float]]]) -> None:
        os.utime(self._full_path(path), times)

    # File Methods
    # ============
    def open(self, path: str, flags: int) -> int:
        return os.open(self._full_path(path), flags)

    def create(self, path: str, mode: int, fi: Optional[Any] = None) -> int:
        uid, gid, _ = fuse.fuse_get_context()
        fd: int = os.open(self._full_path(path), os.O_WRONLY | os.O_CREAT, mode)
        os.chown(self._full_path(path), uid, gid)
        return fd

    def read(self, path: str, length: int, offset: int, fd: int) -> bytes:
        _ = os.lseek(fd, offset, os.SEEK_SET)
        return os.read(fd, length)

    def write(self, path: str, data: bytes, offset: int, fd: int) -> int:
        _ = os.lseek(fd, offset, os.SEEK_SET)
        return os.write(fd, data)

    def truncate(self, path: str, length: int, fd: Optional[int] = None) -> None:
        with open(self._full_path(path), mode="r+") as file:
            _ = file.truncate(length)

    def flush(self, path: str, fd: int) -> None:
        os.fsync(fd)

    def release(self, path: str, fd: int) -> None:
        os.close(fd)

    def fsync(self, path: str, fdatasync: Any, fd: int) -> None:
        self.flush(path, fd)


def main(mount_point: str, root: str) -> None:
    fuse.FUSE(PassThrough(root), mount_point, nothreads=True, foreground=True)


if __name__ == "__main__":
    print(sys.argv)
    main(sys.argv[2], sys.argv[1])
    # NOTE: While working with WSL2 on Windows, we need to use some directory inside /home as our
    # desired mount point.
    # python passthrough.py test_source/dummy_source /home/chandan/test_mount/dummy_mount
