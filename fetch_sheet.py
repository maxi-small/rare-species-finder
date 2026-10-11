#!/usr/bin/env python3
"""Copies the data from the Google Sheet into the three CSV files.

The Google Sheet is where the data is edited. This script downloads its three
published tabs and overwrites species.csv, institutions.csv and holdings.csv,
so any change made to those files directly on GitHub is replaced.

It uses only Python's standard library, so there is nothing to install.
"""

import csv
import io
import sys
import time
import urllib.error
import urllib.request

# The "Publish to web" address of the Sheet, up to and including /pub
PUBLISHED = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSczC-wSPWVAHEFbIsZ6hzBCm6ZGVkyqjLypdk_I3yZPuCGFIu66JAx3IE8pnrkPGAAQG6xCrrE1ZaJ/pub"

# File to write -> (the tab's gid number from its published link,
#                   a heading that tab must have, to catch links that got mixed up)
TABS = {
    "species.csv": ("179681114", "common_name"),
    "institutions.csv": ("1902064476", "lat"),
    "holdings.csv": ("1030903423", "species_id"),
}


def download(gid):
    url = f"{PUBLISHED}?gid={gid}&single=true&output=csv"
    request = urllib.request.Request(url, headers={"User-Agent": "rare-species-finder"})
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8-sig")
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
            time.sleep(3)
    raise RuntimeError(f"could not be downloaded ({last_error}). Is the tab still published to the web?")


def read_tab(file, gid, must_have):
    text = download(gid)
    if text.lstrip().startswith("<"):
        raise RuntimeError("came back as a web page, not CSV. Re-publish the tab as "
                           "Comma-separated values (.csv)")
    rows = [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text))]
    rows = [row for row in rows if any(row)]          # drop blank lines
    if not rows:
        raise RuntimeError("is empty")
    head = [h.lower() for h in rows[0]]
    if must_have not in head:
        raise RuntimeError(f'has no "{must_have}" heading, so this looks like the wrong tab. '
                           f"Its headings are: {', '.join(rows[0])}")
    if len(rows) < 2:
        raise RuntimeError("has headings but no rows. Refusing to publish an empty file")
    return rows


def main():
    tables, problems = {}, []
    for file, (gid, must_have) in TABS.items():
        try:
            tables[file] = read_tab(file, gid, must_have)
        except RuntimeError as e:
            problems.append(f"{file}: the Sheet tab {e}")

    if problems:
        print("Nothing was changed, because the download failed:")
        for p in problems:
            print("  " + p)
            print(f"::error::{p}")
        return 1

    # Only write once all three have arrived, so the files never get out of step.
    for file, rows in tables.items():
        with open(file, "w", newline="", encoding="utf-8") as f:
            csv.writer(f, lineterminator="\n").writerows(rows)
        print(f"{file}: {len(rows) - 1} rows downloaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
