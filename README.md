# idx-price-pipeline

A tiny GitHub repo that keeps ~5 years of daily commodity/FX closes fresh for the
`idx-market-analysis` skill. A scheduled GitHub Action fetches the data and commits
`price-cache/<series>.csv` (format `Date,Close`). The skill pulls these via a
shallow `git clone` — chosen because the Cowork sandbox can reach `github.com` but
NOT `raw.githubusercontent.com`.

## Series covered

`coal` (API2 proxy MTF=F), `brent`, `cpo`, `nickel`, `gold`, `usdidr`.

`pulp` is **not** covered — no free feed exists. Maintain `pulp.csv` by hand from
producer quarterly reports; the pipeline never touches it.

## One-time setup

1. Create a **new public repo** on GitHub named e.g. `idx-price-pipeline`.
   (Public keeps the `git clone` tokenless. Market prices aren't sensitive.)
2. Copy these files into it — keep the paths:
   - `fetch_prices.py`
   - `.github/workflows/update-prices.yml`
   - `price-cache/.gitkeep`
   - `README.md`
3. Commit and push.
4. In the repo: **Settings → Actions → General → Workflow permissions →** set
   **"Read and write permissions"** (lets the Action commit the CSVs back).
5. Go to the **Actions** tab → select **update-prices** → **Run workflow** once
   to seed the CSVs immediately (don't wait for the overnight cron).
6. Copy your repo's clone URL (e.g. `https://github.com/<you>/idx-price-pipeline.git`)
   and paste it into `idx-workspace/remote-cache.txt` so the skill knows where to sync from.

## Schedule

Runs 22:00 UTC Mon–Fri (after the US session, ~05:00 WIB). Adjust the `cron` in
the workflow if you want a different time. You can also trigger it any time with
**Run workflow**.

## Reliability note (honest)

yfinance runs from shared GitHub runner IPs and is occasionally rate-limited. The
fetch script retries with backoff and **fails soft**: a series that won't fetch is
skipped and its previous CSV is left intact — the Action never overwrites good
history with an empty file. If a series goes stale, the skill flags it as
`unverified` rather than trusting an old number silently. If yfinance coverage for
a symbol degrades, swap in a Stooq CSV endpoint in `fetch_prices.py`.
