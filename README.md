# Rare species finder

A map of zoos and aquariums that hold threatened species few other places keep.

**The data in this project is test data. Holdings, dates and display status have not been verified.**

## What each file is

| File | What it is |
|---|---|
| `index.html` | The website. It reads the three data files below when it opens. |
| `species.csv` | One row per species. |
| `institutions.csv` | One row per zoo, aquarium or other place. |
| `holdings.csv` | One row per species kept at a place. This is the file that changes most. |
| `fetch_sheet.py` | Copies the data from the Google Sheet into the three CSV files. |
| `validate.py` | The data check. |
| `.github/workflows/publish.yml` | Tells GitHub to copy the data from the Sheet, run the check, and publish the site only if the check passes. |

## Editing the data

The data is edited in a Google Sheet with three tabs: `species`, `institutions` and `holdings`. The CSV files here are copies of those tabs. **Don't edit the CSV files on GitHub**, because the next run overwrites them with whatever is in the Sheet.

1. Make the change in the Google Sheet.
2. Wait about five minutes. Google's published copy of a Sheet lags behind edits.
3. On GitHub, open the **Actions** tab, choose **Check data and publish site** on the left, and click **Run workflow**.
4. A green tick means the check passed, the CSV files here were updated, and the site has been republished. A red cross means something failed and nothing was changed; click the run to see why.

A new tab in the Sheet isn't published until it is ticked under **File > Share > Publish to web > Published content & settings**.

## What gets included

**Species:** a curated selection of species that are hard to see in zoos and are listed as Endangered, Critically Endangered or Extinct in the Wild on the IUCN Red List. Every known holder is recorded where possible.

**Places** are listed on the site if they meet all four of these:

1. They belong to a recognised zoo association (AZA, EAZA, ZAA, BIAZA, WAZA, CAZA, JAZA, SEAZA, PAAZA, ALPZA, with national bodies case by case), or run an official recovery or rescue programme for the species.
2. They are open to the public.
3. They say publicly that they keep the species. That page is the holding's source link.
4. They treat the species respectfully: no orca shows or circus-style animal acts anywhere at the institution, and the listed species isn't used as a prop.

A holder that fails is still recorded, with `listed` set to `no` and the reason given.

## Columns

### species.csv

| Column | Allowed values |
|---|---|
| `id` | A short name of your choosing, unique, in lowercase letters, numbers, hyphens or underscores. `holdings.csv` refers to it. |
| `common_name` | Any text. |
| `scientific_name` | Any text, unique. |
| `group` | `Mammals`, `Birds`, `Reptiles and amphibians` or `Fish and invertebrates`. |
| `iucn_status` | `EN`, `CR` or `EW`. |
| `subspecies` | `yes` or `no`. |
| `blurb` | One or two sentences. May be empty. |
| `holder_list_complete` | `yes` or `no`. When `no`, the species page says it may be held elsewhere too. May be empty. |

### institutions.csv

| Column | Allowed values |
|---|---|
| `id` | A short unique name, same rules as the species id. |
| `name`, `city`, `country` | Any text. |
| `lat` | Latitude as a decimal number between -90 and 90. North is positive. |
| `lon` | Longitude as a decimal number between -180 and 180. East is positive. |
| `type` | Any text, such as `Zoo`, `Aquarium` or `Breeding centre`. |
| `accreditation` | Any text, such as `EAZA`. May be empty. |
| `listed` | `yes` or `no`. A place set to `no` stays in the data but is left off the site; each species it holds says so in one line. Empty counts as `yes`. |
| `exclusion_reason` | Why the place isn't listed. Required when `listed` is `no`. |

### holdings.csv

| Column | Allowed values |
|---|---|
| `species_id` | An `id` from `species.csv`. |
| `institution_id` | An `id` from `institutions.csv`. |
| `on_display` | `yes` or `no`. |
| `last_verified` | The date the holding was last confirmed, written as `2026-09-14`. Empty if never checked. |
| `source` | A full web address for the evidence, starting with `https://`. May be empty. |

## What the check does

**Errors** stop the site being updated: a missing column or required value, a duplicate id, a holding that points at a species or place that doesn't exist, the same holding entered twice, a status or group outside the allowed list, coordinates that aren't numbers or are out of range, a date in the wrong format or in the future, a source that isn't a web address, and a place set to not listed with no reason given.

**Warnings** are listed but don't stop anything: holdings never checked or not checked for over a year, holdings with no source, species or places with no holdings, species that are off-show everywhere, and species whose every holder is set to not listed.

The check can't tell whether a holding is true. It only catches data the site can't use.
