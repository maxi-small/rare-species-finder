#!/usr/bin/env python3
"""Checks the three data files before the site is published.

Run it from the folder that holds the CSV files:

    python3 validate.py

Errors stop the site being published. Warnings don't, but are worth reading.
It uses only Python's standard library, so there is nothing to install.
"""

import csv
import os
import re
import sys
from datetime import date

# ---- Rules you might want to change ------------------------------------
STATUSES = {"EW", "CR", "EN"}
GROUPS = {"Mammals", "Birds", "Reptiles and amphibians", "Fish and invertebrates"}
STALE_AFTER_DAYS = 365   # a holding not re-checked in this long gets a warning

REQUIRED = {
    "species.csv": ["id", "common_name", "scientific_name", "group", "iucn_status", "subspecies", "blurb"],
    "institutions.csv": ["id", "name", "city", "country", "lat", "lon", "type", "accreditation"],
    "holdings.csv": ["species_id", "institution_id", "on_display", "last_verified", "source"],
}
# Columns that may be left empty.
OPTIONAL = {"blurb", "accreditation", "last_verified", "source"}

ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

errors = []    # (file, row, message)
warnings = []
unlisted = set()   # ids of institutions marked "listed: no"


def error(file, row, message):
    errors.append((file, row, message))


def warn(file, row, message):
    warnings.append((file, row, message))


def load(file):
    """Returns the rows of a CSV file as (row_number, dict) pairs.

    Row numbers match a spreadsheet: the headings are row 1.
    Returns None if the file can't be used at all.
    """
    if not os.path.exists(file):
        error(file, None, "file is missing")
        return None
    try:
        with open(file, newline="", encoding="utf-8-sig") as f:
            table = list(csv.reader(f))
    except UnicodeDecodeError:
        error(file, None, 'not saved as UTF-8. In Excel, save as "CSV UTF-8 (Comma delimited)"')
        return None
    if not table:
        error(file, None, "file is empty")
        return None

    head = [h.strip().lower() for h in table[0]]
    missing = [c for c in REQUIRED[file] if c not in head]
    if missing:
        error(file, 1, "missing column(s): " + ", ".join(missing))
        return None

    rows = []
    for n, cells in enumerate(table[1:], start=2):
        if not any(c.strip() for c in cells):
            continue  # blank line
        if len(cells) > len(head):
            error(file, n, "more cells than headings. A value containing a comma needs double quotes around it")
            continue
        cells = cells + [""] * (len(head) - len(cells))
        row = {h: c.strip() for h, c in zip(head, cells)}
        for col in REQUIRED[file]:
            if not row[col] and col not in OPTIONAL:
                error(file, n, f"{col} is empty")
        rows.append((n, row))
    return rows


def check_id(file, n, col, value, seen):
    if not value:
        return
    if not ID_PATTERN.match(value):
        error(file, n, f'{col} "{value}" should use only lowercase letters, numbers, hyphens and underscores')
    if value in seen:
        error(file, n, f'{col} "{value}" is already used on row {seen[value]}')
    else:
        seen[value] = n


def check_yes_no(file, n, col, value):
    if value and value.lower() not in ("yes", "no"):
        error(file, n, f'{col} is "{value}" but must be yes or no')


def check_species(rows):
    ids, names = {}, {}
    for n, r in rows:
        check_id("species.csv", n, "id", r["id"], ids)
        sci = r["scientific_name"].lower()
        if sci and sci in names:
            error("species.csv", n, f'scientific_name "{r["scientific_name"]}" is already on row {names[sci]}')
        names.setdefault(sci, n)
        if r["iucn_status"] and r["iucn_status"].upper() not in STATUSES:
            error("species.csv", n, f'iucn_status is "{r["iucn_status"]}" but must be one of: ' + ", ".join(sorted(STATUSES)))
        if r["group"] and r["group"] not in GROUPS:
            error("species.csv", n, f'group is "{r["group"]}" but must be one of: ' + ", ".join(sorted(GROUPS)))
        check_yes_no("species.csv", n, "subspecies", r["subspecies"])
        check_yes_no("species.csv", n, "holder_list_complete", r.get("holder_list_complete", ""))
        if not r["blurb"]:
            warn("species.csv", n, f'{r["common_name"] or r["id"]} has no blurb')
    return ids


def check_institutions(rows):
    ids, names = {}, {}
    for n, r in rows:
        check_id("institutions.csv", n, "id", r["id"], ids)
        name = r["name"].lower()
        if name and name in names:
            warn("institutions.csv", n, f'name "{r["name"]}" is also on row {names[name]}. Same place entered twice?')
        names.setdefault(name, n)

        coords = {}
        for col, limit in (("lat", 90), ("lon", 180)):
            try:
                coords[col] = float(r[col])
            except ValueError:
                if r[col]:
                    error("institutions.csv", n, f'{col} is "{r[col]}" but must be a number, like 25.285')
                continue
            if coords[col] != coords[col] or abs(coords[col]) > limit:
                hint = " Are lat and lon the wrong way round?" if col == "lat" else ""
                error("institutions.csv", n, f"{col} is {r[col]} but must be between -{limit} and {limit}.{hint}")
        if coords.get("lat") == 0 and coords.get("lon") == 0:
            warn("institutions.csv", n, f'{r["name"]} is at 0, 0, which is in the Atlantic. Placeholder coordinates?')

        # Optional columns: a place marked "listed: no" is kept in the data but left off the site.
        listed, reason = r.get("listed", ""), r.get("exclusion_reason", "")
        check_yes_no("institutions.csv", n, "listed", listed)
        if listed.lower() == "no":
            unlisted.add(r["id"])
            if not reason:
                error("institutions.csv", n, f'{r["name"]} has listed set to no, so exclusion_reason must say why')
        elif reason:
            warn("institutions.csv", n, f'{r["name"]} has an exclusion_reason but listed is not no, so it still appears on the site')
    return ids


def row_list(numbers):
    """Formats row numbers compactly: [2, 3, 4, 7] becomes 'rows 2-4, 7'."""
    parts, start, prev = [], numbers[0], numbers[0]
    for n in numbers[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        parts.append(str(start) if start == prev else f"{start}-{prev}")
        start = prev = n
    return ("row " if len(numbers) == 1 else "rows ") + ", ".join(parts)


def check_holdings(rows, species_ids, institution_ids):
    today = date.today()
    pairs = {}
    on_show = {}        # species id -> number of places where it is on display
    used_species, used_institutions = set(), set()
    holders, unlisted_holders = {}, {}   # species id -> number of holders, and how many are not listed
    never_checked, no_source = [], []   # row numbers, reported as one line each

    for n, r in rows:
        sp, inst = r["species_id"], r["institution_id"]
        if sp and sp not in species_ids:
            error("holdings.csv", n, f'species_id "{sp}" is not in species.csv')
        if inst and inst not in institution_ids:
            error("holdings.csv", n, f'institution_id "{inst}" is not in institutions.csv')
        if (sp, inst) in pairs:
            error("holdings.csv", n, f"{sp} at {inst} is already on row {pairs[(sp, inst)]}")
        pairs.setdefault((sp, inst), n)
        used_species.add(sp)
        used_institutions.add(inst)
        holders[sp] = holders.get(sp, 0) + 1
        if inst in unlisted:
            unlisted_holders[sp] = unlisted_holders.get(sp, 0) + 1

        check_yes_no("holdings.csv", n, "on_display", r["on_display"])
        if r["on_display"].lower() == "yes":
            on_show[sp] = on_show.get(sp, 0) + 1

        checked = r["last_verified"]
        if not checked:
            never_checked.append(n)
        elif not DATE_PATTERN.match(checked):
            error("holdings.csv", n, f'last_verified is "{checked}" but must look like 2026-09-14. '
                                     "Excel sometimes rewrites dates when it saves")
        else:
            try:
                when = date.fromisoformat(checked)
            except ValueError:
                error("holdings.csv", n, f'last_verified "{checked}" is not a real date')
            else:
                if when > today:
                    error("holdings.csv", n, f"last_verified {checked} is in the future")
                elif (today - when).days > STALE_AFTER_DAYS:
                    warn("holdings.csv", n, f"{sp} at {inst} was last checked {checked}, over {STALE_AFTER_DAYS} days ago")

        if not r["source"]:
            no_source.append(n)
        elif not re.match(r"^https?://\S+$", r["source"]):
            error("holdings.csv", n, f'source "{r["source"]}" must be a full web address starting with http:// or https://')

    if never_checked:
        warn("holdings.csv", None, f"{len(never_checked)} holding(s) have never been checked "
                                   f"(last_verified is empty): {row_list(never_checked)}")
    if no_source:
        warn("holdings.csv", None, f"{len(no_source)} holding(s) have no source link: {row_list(no_source)}")

    for sp, n in species_ids.items():
        if sp not in used_species:
            warn("species.csv", n, f"{sp} has no rows in holdings.csv, so it won't appear on the site")
        elif on_show.get(sp, 0) == 0:
            warn("species.csv", n, f"{sp} is off-show everywhere, so nobody can see it")
        elif holders[sp] <= unlisted_holders.get(sp, 0):
            warn("species.csv", n, f"every holder of {sp} is marked as not listed, so it won't appear on the site")
    for inst, n in institution_ids.items():
        if inst not in used_institutions:
            warn("institutions.csv", n, f"{inst} has no rows in holdings.csv, so it won't appear on the site")


def where(file, row):
    return file if row is None else f"{file} row {row}"


def report(counts):
    lines = []
    if errors:
        lines.append(f"ERRORS ({len(errors)}). These stop the site being published.")
        lines += [f"  {where(f, n)}: {m}" for f, n, m in errors]
        lines.append("")
    if warnings:
        lines.append(f"WARNINGS ({len(warnings)}). These don't stop publishing.")
        lines += [f"  {where(f, n)}: {m}" for f, n, m in warnings]
        lines.append("")
    lines.append("Checked " + ", ".join(f"{v} {k}" for k, v in counts.items()) + ".")
    lines.append("Result: " + ("FAILED" if errors else "passed"))
    print("\n".join(lines))

    # On GitHub, also put the result on the run's summary page and mark the rows.
    if os.environ.get("GITHUB_ACTIONS"):
        for kind, items in (("error", errors), ("warning", warnings)):
            for f, n, m in items:
                print(f"::{kind} file={f},line={n or 1}::{m}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as out:
                out.write("## Data check: " + ("failed, site not updated\n\n" if errors else "passed\n\n"))
                for title, items in (("Errors", errors), ("Warnings", warnings)):
                    if items:
                        out.write(f"### {title} ({len(items)})\n\n")
                        out.writelines(f"- `{where(f, n)}`: {m}\n" for f, n, m in items)
                        out.write("\n")


def main():
    species = load("species.csv")
    institutions = load("institutions.csv")
    holdings = load("holdings.csv")

    species_ids = check_species(species) if species is not None else None
    institution_ids = check_institutions(institutions) if institutions is not None else None
    if holdings is not None and species_ids is not None and institution_ids is not None:
        check_holdings(holdings, species_ids, institution_ids)

    report({
        "species": len(species or []),
        "institutions": len(institutions or []),
        "holdings": len(holdings or []),
    })
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
