#!/usr/bin/env python3
"""THROWAWAY SPIKE, not production code. Probes the Elexon BMRS stream endpoints (ADR-003).

Replaced by the typed, tested ingestion package in PR 2 (ADR-014), then deleted.

Standard library only, nothing to install.

  python3 backend/scripts/spike_elexon.py           # probe: small calls, prints findings
  python3 backend/scripts/spike_elexon.py --full    # also download all raw data to data/raw/

Findings feed back into ADR-003 (ingestion) and ADR-011 (deployment size).
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def get(dataset, params, retries=5):
    """Return (http_code, payload_or_error_text). Retries on 429 and 5xx."""
    url = f"{BASE}/{dataset}/stream?{urllib.parse.urlencode(params, doseq=True)}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")[:300]
            if err.code == 429 or err.code >= 500:
                wait = 2 ** attempt
                print(f"    HTTP {err.code}, retrying in {wait}s")
                time.sleep(wait)
                continue
            return err.code, body
        except urllib.error.URLError as err:
            return 0, str(err)
    return 429, "gave up after retries"


def show(title, code, rows):
    print(f"\n=== {title} ===")
    if code != 200:
        print(f"  FAILED: HTTP {code}: {rows}")
        return False
    print(f"  HTTP 200, {len(rows)} rows")
    if rows:
        print(f"  fields: {sorted(rows[0].keys())}")
        print(f"  first row: {rows[0]}")
    return True


def probe_actuals():
    code, rows = get("FUELHH", {
        "settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-01",
        "fuelType": ["WIND"],
    })
    if not show("FUELHH, WIND, 2026-01-01", code, rows):
        return
    print(f"  distinct fuelType: {sorted({r['fuelType'] for r in rows})}")
    starts = Counter(r["startTime"] for r in rows)
    print(f"  distinct startTime: {len(starts)} (expect 48); max rows per startTime: {max(starts.values())}")
    print(f"  publishTime present: {'publishTime' in rows[0]}")


def probe_forecasts():
    code, rows = get("WINDFOR", {
        "publishDateTimeFrom": "2025-12-31T00:00:00Z",
        "publishDateTimeTo": "2026-01-01T00:00:00Z",
    })
    if not show("WINDFOR, published 2025-12-31 to 2026-01-01", code, rows):
        return
    pubs = Counter(r["publishTime"] for r in rows)
    starts = [r["startTime"] for r in rows]
    horizons = [(parse(r["startTime"]) - parse(r["publishTime"])).total_seconds() / 3600 for r in rows]
    print(f"  distinct publishTime: {len(pubs)}; rows per publishTime (max): {max(pubs.values())}")
    print(f"  startTime range: {min(starts)} to {max(starts)}")
    print(f"  forecast horizon: min {min(horizons):.1f}h, max {max(horizons):.1f}h")
    per_slot = Counter(r["startTime"] for r in rows)
    print(f"  forecasts per startTime: min {min(per_slot.values())}, max {max(per_slot.values())}")
    print(f"  rows in this one day of publishing: {len(rows)}  (x ~47 days is the full-download estimate)")


def probe_range_limit():
    code, rows = get("FUELHH", {
        "settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-31",
        "fuelType": ["WIND"],
    })
    print("\n=== Range limit test: FUELHH WIND for all of January in one call ===")
    if code == 200:
        print(f"  allowed: {len(rows)} rows (expect 1488 = 31 x 48)")
    else:
        print(f"  rejected: HTTP {code}: {rows}")
        print("  -> chunking by week or day is required")


def chunks(start, end, days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def download_full(publish_from):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== FULL DOWNLOAD: FUELHH WIND, 2026-01-01 to 2026-01-31 ===")
    actuals = []
    for a, b in chunks(date(2026, 1, 1), date(2026, 2, 1), 7):
        last = b - timedelta(days=1)
        code, rows = get("FUELHH", {"settlementDateFrom": a.isoformat(),
                                    "settlementDateTo": last.isoformat(), "fuelType": ["WIND"]})
        if code != 200:
            sys.exit(f"  chunk {a}..{last} failed: HTTP {code}: {rows}")
        print(f"  {a}..{last}: {len(rows)} rows")
        actuals.extend(rows)
    path = RAW_DIR / "fuelhh_wind_2026-01.json"
    path.write_text(json.dumps(actuals))
    print(f"  saved {len(actuals)} rows to {path} ({path.stat().st_size / 1e6:.1f} MB)")

    print(f"\n=== FULL DOWNLOAD: WINDFOR, published {publish_from} to 2026-02-01 ===")
    forecasts = []
    start = datetime.fromisoformat(publish_from).replace(tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    for a, b in chunks(start, end, 1):
        code, rows = get("WINDFOR", {"publishDateTimeFrom": iso(a), "publishDateTimeTo": iso(b)})
        if code != 200:
            sys.exit(f"  chunk {a}..{b} failed: HTTP {code}: {rows}")
        print(f"  {a.date()}: {len(rows)} rows")
        forecasts.extend(rows)
    path = RAW_DIR / "windfor_raw.json"
    path.write_text(json.dumps(forecasts))
    print(f"  saved {len(forecasts)} rows to {path} ({path.stat().st_size / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="download all raw data to data/raw/")
    ap.add_argument("--publish-from", default="2025-12-17",
                    help="first publish date to fetch for WINDFOR (default 2025-12-17)")
    args = ap.parse_args()

    probe_actuals()
    probe_forecasts()
    probe_range_limit()
    if args.full:
        download_full(args.publish_from)
    else:
        print("\nProbe done. Paste this whole output back to Claude. Run with --full to download raw data.")


if __name__ == "__main__":
    main()
