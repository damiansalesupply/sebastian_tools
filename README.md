# Ticket comments export

This tool pulls **ticket comments** from the Salesupply API for every shop that has at least one **email recipient** configured in `shops.yml`. It builds one **Excel file per shop**, keeps only comments whose timestamps fall in the **reporting period** you choose, then (unless you turn mailing off) sends each recipient a **zip** containing the files for the shops they are subscribed to.

To use it: configure shops and emails in YAML, set credentials in `.env`, run the script from this folder with **`.venv/bin/python`**, and collect outputs under `data/`.

## What you get

- **Excel files** under `data/<run-date>/`, named like  
  `comments_<ShopName>_<shopId>_<periodStart>_<periodEnd>.xlsx`.
- A **log file** in the same folder:  
  `export_comments_<YYYY-MM-DD_HHMMSS>.log`  
  (the time stamp is when the run started, so multiple runs on the same day do not overwrite each other).
- **Emails** with a zip attachment per recipient (when sending is enabled).

The script asks the API for tickets whose **last change** falls in a wider **inclusive** calendar window than the reporting period (see `--ticket-window-factor`). That window is sent as `fromDateChanged` … `untilDateChanged`, where **`untilDateChanged` is exclusive** on the API side, so the script passes the day *after* the last day you want included. Only **comments inside the reporting period** are written to Excel.

## Requirements

- Python **3.12+** (see `pyproject.toml`) and a virtualenv at **`.venv/`** with project dependencies installed.
- Run the script with **`.venv/bin/python export_comments.py …`** from the project root (use that interpreter so imports match this repo).
- Working directory: project root (where `shops.yml` and `export_comments.py` live).
- **`.env`** (or environment) should include at least:
  - `SHOPCTRL_BASIC_AUTH_HEADER` — CMS API auth (see existing project setup).
  - For email: `EMAIL_PASSWORD`; optionally `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `EMAIL_FROM`, `SMTP_TIMEOUT` (seconds for SMTP socket I/O, default **180**; set to `none` to use the process default, i.e. often no limit).

## Command-line options

| Option | Description |
|--------|-------------|
| `--no-sending` | Only create Excel files and logs; do not send email. |
| `--only-shops SHOP_ID …` | Export only these shop IDs. IDs must already have recipients in `shops.yml`; others are skipped with a warning. Numeric IDs match the CMS shop list (see below). |
| `--only-send-to EMAIL …` | After export, send zips only to these addresses (useful for tests). Unknown addresses are warned. |
| `--period` | Reporting period for **comment timestamps**: `mtd` (default), `last_month`, `last_n_days`, `time-range`. |
| `--n-days N` | With `last_n_days`: **N** calendar days ending on the run day, inclusive (requires `N >= 1`). |
| `--from-date` / `--to-date` | With `time-range`: inclusive bounds, format `YYYY-MM-DD` (`from` must be on or before `to`). |
| `--ticket-window-factor N` | Ticket list API span = (period length in days) × **N** (default `3`). |
| `--shops-yml PATH` | Alternate path to `shops.yml` (default: `./shops.yml`). |

Use `.venv/bin/python export_comments.py --help` for the built-in help text.

## Examples

Run from the project directory.

**Default — month-to-date through today, export and email everyone:**

```bash
.venv/bin/python export_comments.py
```

**Export only, no email:**

```bash
.venv/bin/python export_comments.py --no-sending
```

**Only certain shops (must have recipients in `shops.yml`):**

```bash
.venv/bin/python export_comments.py --only-shops 1521 2040 --no-sending
```

**Previous calendar month:**

```bash
.venv/bin/python export_comments.py --period last_month --no-sending
```

**Last 14 days (inclusive, ending today):**

```bash
.venv/bin/python export_comments.py --period last_n_days --n-days 14
```

**Fixed date range:**

```bash
.venv/bin/python export_comments.py --period time-range --from-date 2026-04-01 --to-date 2026-04-15 --no-sending
```

**Full export but send mail only to one address (smoke test):**

```bash
.venv/bin/python export_comments.py --only-send-to colleague@example.com
```

**Wider ticket search window (factor 5):**

```bash
.venv/bin/python export_comments.py --ticket-window-factor 5
```

## `shops.yml` (short)

Each shop is keyed by numeric ID. Shops with an empty `recipients` list are **not** exported (nothing to send). Add one or more email strings under `recipients` for shops that should appear in the run.

To look up **shop IDs** (same numbers as the keys in `shops.yml`), you can call the CMS API, for example: [https://api.salesupply.com/v1/Shops/](https://api.salesupply.com/v1/Shops/) (GET; use the same `Authorization` value as `SHOPCTRL_BASIC_AUTH_HEADER` in `.env`). The JSON payload includes each shop’s `Id` and name fields.

---

# Brawl Stars account scraper

`brawl_stars_scraper.py` searches game-account marketplaces for **Brawl Stars** listings and filters the ones advertising the **Challenger Colt** skin, to study the second-hand account market. It scrapes **Eldorado.gg**, **G2G.com** and **PlayerAuctions** and writes the results as **JSON** under `data/<run-date>/`.

## How it works

- **Per-site adapters** (`brawl_scraper/sites/`) know how to query each marketplace and normalize its results into a common `Listing` (title, price, currency, url, seller, …). G2G is read from its JSON search API; Eldorado from the page's embedded `__NEXT_DATA__` (or a configurable API); PlayerAuctions from HTML offer cards.
- **Hybrid fetcher** (`brawl_scraper/fetcher.py`): tries plain `requests` first and falls back to a real headless browser (**Playwright**) when a site answers with an anti-bot wall (403/429/503) or needs JavaScript. Playwright is optional and imported lazily — without it the tool still runs the requests-only path. Requests to the same host are rate-limited (`fetch.min_delay`).
- **Filter** (`brawl_scraper/matcher.py`): a listing matches only when the words *challenger* and *colt* appear **adjacent** (either order), after accents/punctuation are normalized — so `Challenger Colt`, `challenger-colt` and `Colt (Challenger)` all match, while "Challenger Shelly … Colt brawler" does **not**.

## Setup

```bash
uv venv --python 3.12
uv pip install -e .            # core deps
uv pip install -e ".[browser]" # optional: enables the Playwright fallback
.venv/bin/playwright install chromium
```

> Note: many marketplaces block datacenter IPs (HTTP 403). Run from an environment/network that can reach the sites, and keep Playwright installed so blocked requests can retry through a real browser.

## Usage

```bash
# All enabled sites (from brawl_config.yml), 3 pages each, results to data/<date>/
.venv/bin/python brawl_stars_scraper.py

# Specific sites, more pages, also keep every scanned listing (not just matches)
.venv/bin/python brawl_stars_scraper.py --sites g2g eldorado --max-pages 5 --save-all

# Requests only (no browser fallback), custom output path
.venv/bin/python brawl_stars_scraper.py --no-browser --output out.json
```

| Option | Description |
|--------|-------------|
| `--sites {eldorado,g2g,playerauctions} …` | Sites to scrape (default: `enabled_sites` from config). |
| `--query` | Search term (default: `brawl stars account`). |
| `--max-pages N` | Max result pages per site (default: 3). |
| `--config PATH` | Config YAML (default: `brawl_config.yml`). |
| `--output PATH` | Output JSON (default: `data/<date>/brawl_colt_<ts>.json`). |
| `--save-all` | Also include every scanned listing, not just Challenger Colt matches. |
| `--no-browser` | Disable the Playwright fallback (requests only). |
| `-q`, `--quiet` | Only log warnings and errors. |

## Configuration (`brawl_config.yml`)

Endpoints, CSS selectors, rate limits and the filter regexes live in `brawl_config.yml`, so a site that changes its markup/API can be fixed there **without code changes**. See the comments in that file.

## Output

A single JSON file: `query`, `filter`, `generated_at`, `stats` (per-site scanned/matched counts) and `matched_listings`. With `--save-all` it also includes `all_listings`. A `.log` file is written alongside it.

