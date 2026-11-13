"""Daily limits and log of paid calls (functional design 6.4 and 8.3): SAM
detections and descriptions by Muse Spark.

Three limits: calls per day in total, calls per day per Commons user, and a
budget in dollars per day. Counts are derived from a JSON Lines log with the
estimated cost of every paid call and, from phase 2, the Commons user name.
"""

import json
import math
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from .detectie.basis import DetectionError

KOSTEN_PER_AFBEELDING = 0.0025  # USD, SAM 3.1 image (docs/meta-sam-api.md)


def kind_of(entry):
    """"sam" (a detection), "beschrijving" ("Wat staat hierop?") or
    "inventaris" ("Wat staat op deze pagina?")."""
    return entry.get("soort") or "sam"


def _readable(entry):
    """Whether a log line is a call the sums can use: an object with a time, and numbers
    (not NaN) for images and cost. A line half written by a crash is skipped, never fatal."""
    if not isinstance(entry, dict) or not isinstance(entry.get("tijd"), str):
        return False
    return all(
        isinstance(entry.get(key, 0), (int, float)) and not isinstance(entry.get(key, 0), bool) and math.isfinite(entry.get(key, 0))
        for key in ("afbeeldingen", "kosten_usd")
    )


def _kinds():
    return {"sam": {"aanroepen": 0, "kosten_usd": 0.0}, "beschrijving": {"aanroepen": 0, "kosten_usd": 0.0}}


class Verbruik:
    def __init__(self, directory, daily_limit, per_user_limit=None, daily_budget=None, now=datetime.now):
        self.directory = Path(directory)
        self.daily_limit = daily_limit
        self.per_user_limit = per_user_limit
        self.daily_budget = daily_budget
        self._now = now
        self._lock = threading.RLock()
        # Paid calls under way: booked before the call, counted by every check,
        # removed once the call is logged (or failed). So parallel requests
        # cannot together pass a limit that each of them alone respects.
        self._reserved = []
        # The log read once per change of the file, not on every question.
        self._cache = (None, [])

    def _today(self):
        return self.day(f"{self._now():%Y-%m-%d}")

    def used_today(self, user=None):
        """Paid calls today (logged and under way), in total or of one Commons user."""
        entries = self._today() + self._reserved
        if user is not None:
            entries = [e for e in entries if e.get("gebruiker") == user]
        return sum(e.get("afbeeldingen", 1) for e in entries)

    def cost_today(self):
        return round(sum(e.get("kosten_usd", 0.0) for e in self._today() + self._reserved), 4)

    @contextmanager
    def reservation(self, needed=1, user=None, cost=0.0):
        """Check the limits and book `needed` calls and `cost` dollars for the
        duration of a paid call; within the block, register() logs the real call."""
        booking = {"afbeeldingen": needed, "kosten_usd": cost, "gebruiker": user}
        with self._lock:
            self.check(needed, user=user, cost=cost)
            self._reserved.append(booking)
        try:
            yield
        finally:
            with self._lock:
                self._reserved = [b for b in self._reserved if b is not booking]

    def reset_at(self):
        tomorrow = (self._now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return tomorrow

    def status(self, user=None):
        used = self.used_today()
        total = self.summary()["totaal"]
        result = {
            "daglimiet": self.daily_limit,
            "gebruikt_vandaag": used,
            "resterend": max(0, self.daily_limit - used),
            "dagbudget_usd": self.daily_budget,
            "kosten_vandaag_usd": self.cost_today(),
            "reset": self.reset_at().isoformat(timespec="minutes"),
            "totaal_aanroepen": total["aanroepen"],
            "totaal_kosten_usd": total["kosten_usd"],
            "per_model": self._per_model(),
        }
        if user is not None and self.per_user_limit is not None:
            mine = self.used_today(user)
            result["gebruiker"] = {
                "naam": user,
                "daglimiet": self.per_user_limit,
                "gebruikt_vandaag": mine,
                "resterend": max(0, self.per_user_limit - mine),
            }
        return result

    def _per_model(self):
        """Calls and costs today and in total, for SAM and for Muse Spark
        (descriptions and page overviews together)."""
        today = f"{self._now():%Y-%m-%d}"
        result = {m: {"vandaag_aanroepen": 0, "vandaag_kosten_usd": 0.0, "totaal_aanroepen": 0, "totaal_kosten_usd": 0.0} for m in ("sam", "muse")}
        for entry in self.entries():
            totals = result["sam" if kind_of(entry) == "sam" else "muse"]
            calls, amount = entry.get("afbeeldingen", 1), entry.get("kosten_usd", 0.0)
            totals["totaal_aanroepen"] += calls
            totals["totaal_kosten_usd"] += amount
            if entry["tijd"][:10] == today:
                totals["vandaag_aanroepen"] += calls
                totals["vandaag_kosten_usd"] += amount
        for totals in result.values():
            totals["vandaag_kosten_usd"] = round(totals["vandaag_kosten_usd"], 4)
            totals["totaal_kosten_usd"] = round(totals["totaal_kosten_usd"], 4)
        return result

    def check(self, needed=1, user=None, cost=0.0):
        """Raise (HTTP 429) when `needed` more calls, or `cost` more dollars,
        would exceed today's total limit, the user's limit or the budget."""
        wait = self._wait_text()
        used = self.used_today()
        if used + needed > self.daily_limit:
            raise DetectionError(
                f"Daglimiet bereikt ({used} van {self.daily_limit} betaalde aanroepen vandaag"
                + (f"; deze opdracht vraagt er {needed}" if needed > 1 else "")
                + f"). {wait}",
                status=429,
                code="daily_limit",
            )
        if user is not None and self.per_user_limit is not None:
            mine = self.used_today(user)
            if mine + needed > self.per_user_limit:
                raise DetectionError(
                    f"Je daglimiet is bereikt ({mine} van {self.per_user_limit} betaalde aanroepen vandaag). {wait}",
                    status=429,
                    code="user_limit",
                )
        if self.daily_budget is not None:
            spent = self.cost_today()
            if spent + cost > self.daily_budget:
                raise DetectionError(
                    f"Dagbudget bereikt (${spent:.2f} van ${self.daily_budget:.2f} vandaag). {wait}",
                    status=429,
                    code="daily_budget",
                )

    def _wait_text(self):
        remaining = self.reset_at() - self._now()
        hours, minutes = divmod(int(remaining.total_seconds()) // 60, 60)
        return f"Nieuwe aanroepen kunnen over {hours} uur en {minutes} minuten."

    # -- Log ---------------------------------------------------------------------

    def entries(self):
        """All logged paid calls, oldest first. Unreadable lines are skipped."""
        path = self.directory / "logboek.jsonl"
        if not path.exists():
            return []
        stat = path.stat()
        key = (stat.st_mtime_ns, stat.st_size)
        if self._cache[0] == key:
            return list(self._cache[1])
        result = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if _readable(entry):
                result.append(entry)
        self._cache = (key, result)
        return list(result)

    def summary(self, start=None, end=None):
        """Totals overall and per day (newest first), also per kind of call
        (`per_soort`: "sam" or "beschrijving"); `start`/`end` are inclusive
        dates as 'YYYY-MM-DD'."""
        days = {}
        for entry in self.entries():
            day = entry["tijd"][:10]
            if (start and day < start) or (end and day > end):
                continue
            totals = days.setdefault(day, {"datum": day, "aanroepen": 0, "kosten_usd": 0.0, "per_soort": _kinds()})
            calls, amount = entry.get("afbeeldingen", 1), entry.get("kosten_usd", 0.0)
            totals["aanroepen"] += calls
            totals["kosten_usd"] += amount
            kind = totals["per_soort"].setdefault(kind_of(entry), {"aanroepen": 0, "kosten_usd": 0.0})
            kind["aanroepen"] += calls
            kind["kosten_usd"] += amount
        per_day = sorted(days.values(), key=lambda d: d["datum"], reverse=True)
        overall = _kinds()
        for totals in per_day:
            totals["kosten_usd"] = round(totals["kosten_usd"], 4)
            for name, kind in totals["per_soort"].items():
                overall.setdefault(name, {"aanroepen": 0, "kosten_usd": 0.0})
                overall[name]["aanroepen"] += kind["aanroepen"]
                overall[name]["kosten_usd"] += kind["kosten_usd"]
                kind["kosten_usd"] = round(kind["kosten_usd"], 4)
        for kind in overall.values():
            kind["kosten_usd"] = round(kind["kosten_usd"], 4)
        return {
            "totaal": {
                "aanroepen": sum(d["aanroepen"] for d in per_day),
                "kosten_usd": round(sum(d["kosten_usd"] for d in per_day), 4),
                "dagen": len(per_day),
                "per_soort": overall,
            },
            "per_dag": per_day,
        }

    def day(self, date):
        """The logged calls of one day ('YYYY-MM-DD'), oldest first."""
        return [e for e in self.entries() if e["tijd"][:10] == date]

    def register(self, entry, images=1, cost=None, user=None):
        """Log a paid call. `cost` (USD) overrides the SAM price per image, e.g.
        for token-priced descriptions; `user` is the Commons user name (phase 2)."""
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            record = {
                "tijd": self._now().isoformat(timespec="seconds"),
                "afbeeldingen": images,
                "kosten_usd": round(images * KOSTEN_PER_AFBEELDING if cost is None else cost, 6),
                "gebruiker": user,
                **entry,
            }
            path = self.directory / "logboek.jsonl"
            with open(path, "a+b") as log:
                # A last line cut off by a crash gets its line end first, so this call
                # is not glued to it (and lost with it).
                log.seek(0, 2)
                start = b""
                if log.tell():
                    log.seek(-1, 2)
                    start = b"" if log.read(1) == b"\n" else b"\n"
                log.write(start + (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
