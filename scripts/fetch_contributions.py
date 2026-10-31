#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions fragment
(the same HTML your profile page loads, no token needed) and write
data/contributions.json with the raw days plus streaks, best day and monthly totals.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from common import DATA, PROFILE

USER = os.environ.get("GH_PROFILE_USER", PROFILE["username"])


def fetch_days():
    resp = requests.get(f"https://github.com/users/{USER}/contributions",
                        headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        if not td.get("data-date"):
            continue
        m = re.match(r"(\d[\d,]*)", tips.get(td.get("id"), ""))
        days.append({"date": td["data-date"],
                     "count": int(m.group(1).replace(",", "")) if m else 0,
                     "level": int(td.get("data-level") or 0)})
    if not days:
        sys.exit("no calendar cells found -- wrong username, or GitHub changed its markup")
    return sorted(days, key=lambda d: d["date"])


def current_streak(days):
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1  # today isn't over yet -- don't break the streak on it
    end = i
    while i >= 0 and days[i]["count"] > 0:
        i -= 1
    n = end - i
    return {"length": n, "start": days[i + 1]["date"] if n else None, "end": days[end]["date"] if n else None}


def longest_streak(days):
    best = {"length": 0, "start": None, "end": None}
    run_start = None
    for i, d in enumerate(days):
        if d["count"] == 0:
            run_start = None
            continue
        run_start = i if run_start is None else run_start
        if i - run_start + 1 > best["length"]:
            best = {"length": i - run_start + 1, "start": days[run_start]["date"], "end": d["date"]}
    return best


def build(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "username": USER,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w") as f:
        json.dump(data, f, indent=2)
    print(f"{USER}: {data['total_contributions']} contributions, "
          f"streak {data['current_streak']['length']} (longest {data['longest_streak']['length']})")
