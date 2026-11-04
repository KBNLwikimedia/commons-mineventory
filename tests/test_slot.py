"""The lock of the object stores holds across threads and processes (cutter/slot.py),
so the cleanup task and the app never overwrite each other's change."""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from cutter.opruimen import Cleanup
from cutter.slot import LockTimeout, ProcessLock, store_lock

from test_opruimen import NOW, tree

ROOT = Path(__file__).resolve().parents[1]


def test_the_lock_is_reentrant_in_one_thread(tmp_path):
    lock = store_lock(tmp_path)
    with lock:
        with lock:  # a locked method that calls another
            pass
    with lock:
        pass


def test_a_second_holder_waits_and_gives_up_after_the_timeout(tmp_path):
    with store_lock(tmp_path):
        other = ProcessLock(tmp_path / ".slot", timeout=0.2)  # its own file handle, as another worker
        with pytest.raises(LockTimeout):
            other.acquire()
    with ProcessLock(tmp_path / ".slot", timeout=0.2):
        pass  # free again


def test_the_lock_holds_against_another_process(tmp_path):
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import sys; from cutter.slot import store_lock; l = store_lock(sys.argv[1]); l.acquire(); "
         "print('vast', flush=True); sys.stdin.read(); l.release()", str(tmp_path)],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "vast"
        with pytest.raises(LockTimeout):
            ProcessLock(tmp_path / ".slot", timeout=0.2).acquire()
        holder.stdin.close()  # the other process lets go
        holder.wait(timeout=10)
        with ProcessLock(tmp_path / ".slot", timeout=5):
            pass
    finally:
        holder.kill()


def test_the_cleanup_waits_for_the_app_and_keeps_its_edit(tmp_path):
    cache, output, page = tree(tmp_path, cutout_age=40)
    store_path = page / "objecten.json"
    app_lock = store_lock(output)  # the app, as another process would hold it
    app_lock.acquire()
    cleanup = threading.Thread(target=Cleanup(cache, output, now=NOW).run, kwargs={"apply": True})
    cleanup.start()
    time.sleep(0.3)
    assert cleanup.is_alive() and (page / "jpg" / "a.jpg").exists()  # waiting for the app
    # The app edits the page meanwhile and writes objecten.json.
    store = json.loads(store_path.read_text(encoding="utf-8"))
    store["objecten"][0]["bijschrift"] = "met de hand"
    store_path.write_text(json.dumps(store), encoding="utf-8")
    app_lock.release()
    cleanup.join(timeout=10)
    assert not cleanup.is_alive()
    store = json.loads(store_path.read_text(encoding="utf-8"))
    assert store["objecten"][0]["bijschrift"] == "met de hand"  # the edit is kept
    assert "opgeslagen" not in store["objecten"][0]  # and the cleanup did its work
    assert not (page / "jpg" / "a.jpg").exists()


def test_a_trial_run_does_not_wait_for_the_lock(tmp_path):
    cache, output, page = tree(tmp_path, cutout_age=40)
    with store_lock(output):
        report = Cleanup(cache, output, now=NOW).run()  # only counts: no lock needed
    assert report["uitsneden"]["bestanden"] == 5
