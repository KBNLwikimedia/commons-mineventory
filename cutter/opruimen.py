"""Cleanup of stored files by retention period (functional design 12.1).

The periods count from the last use, not from creation. A file is "used" when
the app reads it; the app then sets its access time (`mark_used`) and leaves
the modification time alone, because the Commons cache uses that to decide
whether an answer is still fresh. The last use is the later of the two.

What goes when (defaults; BEWAAR_* in the configuration):

- originals and the Commons cache (API answers, page images): BEWAAR_ORIGINELEN_DAGEN (7).
  Both are on Commons and free to fetch again.
- cut-outs and masks that are not on Commons yet: BEWAAR_UITSNEDEN_DAGEN (30).
  The saved files of an object go, and the object forgets it was saved
  (saving it again makes them anew); previews and decoded masks in the cache too.
- detections and descriptions: BEWAAR_CACHE_DAGEN (365). The answers of SAM
  and Muse Spark in the cache, and a page's objects (objecten.json) when the
  page was not opened in that time.

The usage log (uitvoer/verbruik) is never removed. Without `apply` nothing is
deleted: the result only says what would go.
"""

import json
import os
import shutil
import time
from pathlib import Path

DAY = 86400
# Objects that are on Commons keep their record; the file on Commons is the lasting copy.
UPLOADED_KEYS = ("upload", "commons_url")
CUTOUT_DIRS = ("jpg", "png", "maskers")


def mark_used(path):
    """Note that `path` was just used: access time now, modification time kept."""
    try:
        os.utime(path, (time.time(), Path(path).stat().st_mtime))
    except OSError:
        pass  # a read-only disk or a file that just went: the cleanup is a little early


def last_used(path):
    stat = Path(path).stat()
    return max(stat.st_mtime, stat.st_atime)


class Cleanup:
    def __init__(self, cache_dir, output_dir, days_originals=7, days_cutouts=30, days_cache=365, now=None):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.days = {"originelen": days_originals, "uitsneden": days_cutouts, "cache": days_cache}
        self.now = now if now is not None else time.time()
        self.report = {kind: {"bestanden": 0, "bytes": 0} for kind in self.days}
        self.apply = False

    @classmethod
    def from_config(cls, config, now=None):
        return cls(
            config.CACHE_DIR,
            config.UITVOER_DIR,
            config.BEWAAR_ORIGINELEN_DAGEN,
            config.BEWAAR_UITSNEDEN_DAGEN,
            config.BEWAAR_CACHE_DAGEN,
            now=now,
        )

    def _expired(self, path, kind):
        return self.now - last_used(path) > self.days[kind] * DAY

    def _remove(self, path, kind):
        self.report[kind]["bestanden"] += 1
        self.report[kind]["bytes"] += path.stat().st_size
        if self.apply:
            path.unlink()

    def _files(self, folder):
        return [p for p in Path(folder).rglob("*") if p.is_file()] if Path(folder).is_dir() else []

    def run(self, apply=False):
        """Remove (with `apply`) or count everything past its period. Returns
        per kind how many files and bytes, and whether anything was deleted."""
        self.apply = apply
        cache_kind = {"originelen": "originelen", "commons": "originelen", "uitsneden": "uitsneden", "maskers": "uitsneden"}
        if self.cache_dir.is_dir():
            for folder in sorted(p for p in self.cache_dir.iterdir() if p.is_dir()):
                kind = cache_kind.get(folder.name, "cache")  # detectie, beschrijvingen and anything else
                for path in self._files(folder):
                    if self._expired(path, kind):
                        self._remove(path, kind)
        if self.output_dir.is_dir():
            for file_dir in sorted(p for p in self.output_dir.iterdir() if p.is_dir() and p.name != "verbruik"):
                self._clean_file_dir(file_dir)
        if apply:
            self._remove_empty_dirs(self.cache_dir)
        return {"verwijderd": apply, "dagen": dict(self.days), **self.report}

    def _clean_file_dir(self, file_dir):
        pages = sorted(p for p in file_dir.iterdir() if p.is_dir() and p.name.startswith("pagina_"))
        for page in pages:
            store_path = page / "objecten.json"
            files = self._files(page)
            # The whole page (its objects and descriptions) after BEWAAR_CACHE_DAGEN without use.
            if files and all(self._expired(p, "cache") for p in files):
                for path in files:
                    self._remove(path, "cache")
                if self.apply:
                    shutil.rmtree(page, ignore_errors=True)
                continue
            self._clean_cutouts(page, store_path)
        if self.apply and not any(p.name.startswith("pagina_") for p in file_dir.iterdir() if p.is_dir()):
            shutil.rmtree(file_dir, ignore_errors=True)  # bestand.json alone: the file is gone

    def _clean_cutouts(self, page, store_path):
        """Saved cut-outs past BEWAAR_UITSNEDEN_DAGEN; their objects forget them."""
        store = json.loads(store_path.read_text(encoding="utf-8")) if store_path.exists() else {}
        objects = store.get("objecten", []) + store.get("prullenbak", [])
        # Every file an object refers to, before any object forgets its own.
        known = {page.parent / v for o in objects for k, v in (o.get("opgeslagen") or {}).items() if k in ("jpg", "png", "masker")}
        changed = False
        for obj in objects:
            saved = obj.get("opgeslagen")
            if not saved or any(obj.get(k) for k in UPLOADED_KEYS):
                continue
            paths = [page.parent / saved[k] for k in ("jpg", "png", "masker") if saved.get(k)]
            present = [p for p in paths if p.exists()]
            if present and all(self._expired(p, "uitsneden") for p in present):
                for path in present:
                    self._remove(path, "uitsneden")
                obj.pop("opgeslagen")
                changed = True
        # Files no object refers to any more (an object that was deleted).
        for sub in CUTOUT_DIRS:
            for path in self._files(page / sub):
                if path not in known and self._expired(path, "uitsneden"):
                    self._remove(path, "uitsneden")
        if changed and self.apply:
            tmp = store_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(store_path)

    def _remove_empty_dirs(self, root):
        if not Path(root).is_dir():
            return
        for folder in sorted((p for p in Path(root).rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            try:
                folder.rmdir()  # only when empty
            except OSError:
                pass


def summary(report):
    """The report in a few lines of Dutch, for the command line and the log."""
    verb = "Verwijderd" if report["verwijderd"] else "Zou weggaan (proef; met --echt wordt het verwijderd)"
    names = {"originelen": "originelen en Commons-cache", "uitsneden": "uitsneden en maskers", "cache": "detecties en beschrijvingen"}
    lines = [f"{verb}:"]
    for kind, name in names.items():
        item = report[kind]
        lines.append(f"- {name} (na {report['dagen'][kind]} dagen): {item['bestanden']} bestanden, {item['bytes'] / 1e6:.1f} MB")
    return "\n".join(lines)
