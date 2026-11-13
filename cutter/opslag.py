"""Safe reading and writing of the app's JSON files and caches.

One place for what every store needs (backlog: a more robust backend):

- `write_atomic`: write via a temporary file of its own and a rename, so a reader
  sees the old or the new file, never half of one (a crash, a full disk). On
  Windows the rename is retried a few times: a virus scanner or a reader can
  hold the target for a moment (PermissionError).
- `read_json`: a missing file (also one removed between exists() and read) is
  the default; an unreadable one (empty, half written, not JSON, the wrong shape)
  is kept aside as `<name>.kapot-<hash>` and is either the default or a
  CorruptFile error, as the caller chooses. User data is never silently lost:
  the copy stays until someone looks at it.
"""

import hashlib
import json
import logging
import os
import shutil
import threading
import time
from pathlib import Path

from .detectie.basis import DetectionError

logger = logging.getLogger(__name__)

REPLACE_ATTEMPTS = 5
REPLACE_WAIT = 0.05  # seconds, growing per attempt
CORRUPT_MARK = ".kapot-"


class CorruptFile(DetectionError):
    """A store or cache file that cannot be read (500, code corrupt_file)."""

    def __init__(self, path, copy=None):
        where = f" Een kopie staat in {copy.name}." if copy else ""
        super().__init__(f"Het bestand {Path(path).name} is beschadigd en kan niet gelezen worden.{where}", status=500, code="corrupt_file")
        self.path = Path(path)
        self.copy = copy


def _replace(tmp, path, sleep=time.sleep):
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            sleep(REPLACE_WAIT * (attempt + 1))


def write_atomic(path, data):
    """Write `data` (text as UTF-8, or bytes) to `path` atomically; makes the folder.
    The temporary file is unique per process and thread, so two writers never share it,
    and it is removed again when writing fails (a full disk)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}-{threading.get_ident()}.tmp")
    try:
        if isinstance(data, str):
            tmp.write_text(data, encoding="utf-8")
        else:
            tmp.write_bytes(data)
        _replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def write_json(path, data, indent=2):
    write_atomic(path, json.dumps(data, ensure_ascii=False, indent=indent))


def keep_copy(path):
    """Copy an unreadable file to `<name>.kapot-<hash>` next to it (once per content);
    returns the copy, or None for an empty file or when copying fails."""
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data.strip():
        return None
    copy = path.with_name(f"{path.name}{CORRUPT_MARK}{hashlib.sha1(data).hexdigest()[:10]}")
    if copy.exists():
        return copy
    try:
        shutil.copyfile(path, copy)
    except OSError:
        return None
    logger.warning("Unreadable file %s kept as %s", path, copy.name)
    return copy


def read_json(path, default=None, valid=None, corrupt="default", copy=True):
    """The JSON in `path`, or `default` when it does not exist (also when it went just now).
    `valid` (a function) checks the shape. An unreadable or invalid file is kept aside
    (with `copy`) and gives `default` (corrupt="default") or raises CorruptFile ("raise")."""
    path = Path(path)
    try:
        text = path.read_bytes().decode("utf-8")
        data = json.loads(text)
        if valid is not None and not valid(data):
            raise ValueError("unexpected shape")
    except FileNotFoundError:
        return default
    except (ValueError, UnicodeDecodeError, RecursionError):
        kept = keep_copy(path) if copy else None
        if corrupt == "raise":
            raise CorruptFile(path, kept) from None
        logger.warning("Unreadable file %s: using the default", path)
        return default
    return data


def valid_store(data):
    """The shape of an object store (objecten.json): an object whose lists hold objects with an id."""
    return isinstance(data, dict) and all(
        isinstance(data.get(key, []), list) and all(isinstance(o, dict) and isinstance(o.get("id"), str) for o in data.get(key, []))
        for key in ("objecten", "prullenbak")
    )


def read_store(path, corrupt="default", copy=True):
    """objecten.json, or {} when missing. An unreadable one is kept aside as
    objecten.json.kapot-<hash> and counts as empty, so the page stays usable."""
    return read_json(path, {}, valid=valid_store, corrupt=corrupt, copy=copy)
