"""A lock that holds across threads and processes.

The app writes the object stores (objecten.json) under one lock. The cleanup
task (`flask --app app opruimen --echt`) is a separate process, and on
Toolforge the web service can run several workers: a threading lock alone
cannot keep them apart. ProcessLock adds an operating-system lock on a small
file (uitvoer/.slot), so a store is read, changed and written as one step,
whoever does it.

Re-entrant like threading.RLock: locked methods call each other.
"""

import os
import threading
import time
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl

WAIT = 0.05  # seconds between attempts
TIMEOUT = 120  # longer than any write; a lock held this long is a stuck process


class LockTimeout(RuntimeError):
    pass


class ProcessLock:
    def __init__(self, path, timeout=TIMEOUT):
        self.path = Path(path)
        self.timeout = timeout
        self._thread = threading.RLock()
        self._depth = 0
        self._handle = None

    def acquire(self):
        self._thread.acquire()
        if self._depth == 0:
            try:
                self._lock_file()
            except BaseException:
                self._thread.release()
                raise
        self._depth += 1
        return True

    def release(self):
        self._depth -= 1
        if self._depth == 0:
            self._unlock_file()
        self._thread.release()

    __enter__ = acquire

    def __exit__(self, *exc):
        self.release()

    def _lock_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+b")
        try:
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    if os.name == "nt":
                        # msvcrt locks a byte range; byte 0 of the file is the lock.
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise LockTimeout(f"{self.path} is al {self.timeout} s bezet.") from None
                    time.sleep(WAIT)
        except BaseException:
            handle.close()
            raise
        self._handle = handle

    def _unlock_file(self):
        handle, self._handle = self._handle, None
        try:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def store_lock(output_dir):
    """The one lock for the object stores under `output_dir` (the app and the cleanup)."""
    return ProcessLock(Path(output_dir) / ".slot")
