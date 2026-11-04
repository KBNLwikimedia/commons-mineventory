"""Cleanup by retention period (functional design 12.1), on a made-up folder tree."""

import json
import os
import time

from cutter.opruimen import DAY, Cleanup, last_used, mark_used, summary

NOW = time.time()


def write(path, data=b"x", age_days=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data) if isinstance(data, bytes) else path.write_text(data, encoding="utf-8")
    stamp = NOW - age_days * DAY
    os.utime(path, (stamp, stamp))
    return path


def tree(tmp_path, page_age=0, cutout_age=0):
    cache, output = tmp_path / "cache", tmp_path / "uitvoer"
    write(cache / "originelen" / "ab" / "abc", age_days=8)
    write(cache / "originelen" / "cd" / "cde", age_days=2)
    write(cache / "commons" / "ef" / "efg", age_days=10)
    write(cache / "uitsneden" / "12" / "123.jpg", age_days=31)
    write(cache / "detectie" / "34" / "345.json", age_days=366)
    write(cache / "beschrijvingen" / "56" / "567.json", age_days=100)
    page = output / "M1" / "pagina_1"
    store = {
        "objecten": [
            {"id": "a", "opgeslagen": {"jpg": "pagina_1/jpg/a.jpg", "png": "pagina_1/png/a.png", "masker": "pagina_1/maskers/a_mask.png"}},
            {"id": "b", "opgeslagen": {"jpg": "pagina_1/jpg/b.jpg"}, "upload": {"titel": "File:B.jpg"}},
        ],
        "prullenbak": [],
    }
    write(page / "objecten.json", json.dumps(store), age_days=page_age)
    for name in ("jpg/a.jpg", "png/a.png", "maskers/a_mask.png", "jpg/b.jpg", "jpg/weg.jpg"):
        write(page / name, age_days=cutout_age)
    write(output / "M1" / "bestand.json", "{}", age_days=page_age)
    write(output / "verbruik" / "logboek.jsonl", "{}", age_days=1000)
    return cache, output, page


def test_trial_run_counts_but_keeps_everything(tmp_path):
    cache, output, page = tree(tmp_path, cutout_age=40)
    report = Cleanup(cache, output, now=NOW).run()
    assert not report["verwijderd"]
    assert report["originelen"]["bestanden"] == 2  # the old original and the old Commons answer
    assert report["uitsneden"]["bestanden"] == 5  # preview, a's three files and the orphan; not the uploaded b
    assert report["cache"]["bestanden"] == 1  # the year-old detection
    assert (cache / "originelen" / "ab" / "abc").exists() and (page / "jpg" / "a.jpg").exists()
    assert "proef" in summary(report)


def test_apply_removes_by_period_and_the_object_forgets_its_files(tmp_path):
    cache, output, page = tree(tmp_path, cutout_age=40)
    Cleanup(cache, output, now=NOW).run(apply=True)
    assert not (cache / "originelen" / "ab").exists() and (cache / "originelen" / "cd" / "cde").exists()
    assert not (cache / "detectie" / "34").exists() and (cache / "beschrijvingen" / "56" / "567.json").exists()
    assert not (page / "jpg" / "a.jpg").exists() and not (page / "jpg" / "weg.jpg").exists()
    assert (page / "jpg" / "b.jpg").exists()  # on Commons: kept
    store = json.loads((page / "objecten.json").read_text(encoding="utf-8"))
    assert "opgeslagen" not in store["objecten"][0] and store["objecten"][1]["opgeslagen"]
    assert (output / "verbruik" / "logboek.jsonl").exists()


def test_a_page_not_opened_for_a_year_goes_entirely(tmp_path):
    cache, output, page = tree(tmp_path, page_age=400, cutout_age=400)
    Cleanup(cache, output, now=NOW).run(apply=True)
    assert not (output / "M1").exists()
    assert (output / "verbruik" / "logboek.jsonl").exists()


def test_mark_used_keeps_the_modification_time(tmp_path):
    path = write(tmp_path / "f", age_days=50)
    mtime = path.stat().st_mtime
    mark_used(path)
    assert path.stat().st_mtime == mtime
    assert NOW - last_used(path) < 60
