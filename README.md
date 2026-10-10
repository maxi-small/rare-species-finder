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
| `validate.py` | The data check. |
| `.github/workflows/publish.yml` | Tells GitHub to run the check on every change and publish the site only if it passes. |

## Editing the data

1. Open a data file on GitHub and click the pencil icon.
2. Make the change and click **Commit changes**.
3. Open the **Actions** tab. A green tick means the check passed and the site has been updated. A red cross means the check found an error and the site has been left as it was; click the run to see which row.

A value that contains a comma needs double quotes around it, for example `"Found only on Borneo, in mangroves and riverside forest."`

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

### institutions.csv

| Column | Allowed values |
|---|---|
| `id` | A short unique name, same rules as the species id. |
| `name`, `city`, `country` | Any text. |
| `lat` | Latitude as a decimal number between -90 and 90. North is positive. |
| `lon` | Longitude as a decimal number between -180 and 180. East is positive. |
| `type` | Any text, such as `Zoo`, `Aquarium` or `Breeding centre`. |
| `accreditation` | Any text, such as `EAZA`. May be empty. |

### holdings.csv

| Column | Allowed values |
|---|---|
| `species_id` | An `id` from `species.csv`. |
| `institution_id` | An `id` from `institutions.csv`. |
| `on_display` | `yes` or `no`. |
| `last_verified` | The date the holding was last confirmed, written as `2026-09-14`. Empty if never checked. |
| `source` | A full web address for the evidence, starting with `https://`. May be empty. |

## What the check does

**Errors** stop the site being updated: a missing column or required value, a duplicate id, a holding that points at a species or place that doesn't exist, the same holding entered twice, a status or group outside the allowed list, coordinates that aren't numbers or are out of range, a date in the wrong format or in the future, and a source that isn't a web address.

**Warnings** are listed but don't stop anything: holdings never checked or not checked for over a year, holdings with no source, species or places with no holdings, species that are off-show everywhere, and species on display at more than 10 places.

The check can't tell whether a holding is true. It only catches data the site can't use.
