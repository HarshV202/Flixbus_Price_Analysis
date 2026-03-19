# Bus Pricing Analysis System

A Python-based pipeline that identifies comparable competitor buses for every Flixbus listing and flags pricing issues — automatically, daily, at scale.

Dataset : https://drive.google.com/drive/folders/1QQboE8IV9OP2h0Z3oqwHWC9T3ogG7dQO?usp=sharing
---

## Overview

This system solves two problems:

1. **Similar Bus Identification** — For each Flixbus listing, find a pool of genuinely comparable competitor buses using a three-tier similarity framework
2. **Price Flagging** — Compare Flixbus prices against the peer median and flag listings that are too high or too low, accounting for demand and platform visibility signals

**Dataset:** 850,000+ rows of route-level bus listings across multiple routes and departure dates  
**Operator:** Flixbus (identified by operator name in dataset)  
**Benchmark metric:** Weighted Average Price (WAP)

---

## Key Results

| Metric | Value |
|--------|-------|
| Flixbus listings processed | 31,110 |
| Listings with comparable pool | 24,666 (79.3%) |
| Comparable pairs generated | 201,989 |
| Median WAP vs peer median | -13.6% |
| Flag rate | 53.6% |
| Flagged TOO LOW | 8,623 |
| Flagged TOO HIGH | 4,606 |
| CRITICAL flags | 5,808 |

> **Key finding:** Flixbus is systematically underpriced — TOO LOW flags outnumber TOO HIGH 2:1, with a median price 13.6% below comparable peers.

---

## Project Structure

```
pricing_pipeline/
    dataset.xlsx                    ← daily input file
    similarity.py                   ← Task 1: similar bus matching
    flagging.py                     ← Task 2: price flagging
    build_final_workbook.py         ← consolidates outputs into final Excel
    run_pipeline.py                 ← master script (calls all three)
    outputs/
        pricing_analysis_YYYY-MM-DD.xlsx
    logs/
        pipeline_YYYY-MM-DD.log
```

---

## Installation

**Requirements:** Python 3.8+

```bash
pip install pandas openpyxl
```

---

## Usage

### Run the full pipeline

Place `dataset.xlsx` in the project folder, then run:

```bash
python run_pipeline.py
```

This calls all three scripts in sequence and produces `pricing_analysis_final.xlsx`.

### Run individual steps

```bash
# Step 1 — similar bus matching
python similarity.py

# Step 2 — price flagging (requires similarity_output.xlsx)
python flagging.py

# Step 3 — build consolidated Excel report
python build_final_workbook.py
```

---

## Output

`pricing_analysis_final.xlsx` contains five sheets:

| Sheet | Contents |
|-------|----------|
| Sheet 1 – Flagging Output | Every Flixbus listing with flag status, direction, severity, confidence, dynamic thresholds, load factor, and rank signal. Colour-coded: red = TOO HIGH, amber = TOO LOW, green = OK |
| Sheet 2 – Logic Explanation | Full written documentation of the similarity and flagging logic with all assumptions |
| Sheet 3 – Comparables | Every matched competitor pair with delta values for departure time, duration, and rating |
| Sheet 4 – Summary Stats | Top-level flag counts and direction × severity breakdown |
| Sheet 5 – Automation Plan | MVP automation plan with scheduling options and folder structure |

---

## How It Works

### Task 1 — Similar Bus Identification

Competitors are matched to each Flixbus listing using a three-tier framework:

**Tier 1 — Hard Filters (exact match)**

| Field | Rationale |
|-------|-----------|
| Route Number | Cannot compare prices across different origin-destination pairs |
| Departure Date | Different dates reflect different demand conditions |
| Product Key (AC + Bus Type) | AC_Sleeper, AC_Mixed, NonAC_Seater etc. — customers don't cross-shop across these |

**Tier 2 — Soft Filters (range match)**

| Field | Tolerance | Rationale |
|-------|-----------|-----------|
| Departure Time | ± 90 min | Travellers compare buses within a realistic ±90 min window |
| Journey Duration | ± 45 min | Beyond 45 min, route differences justify independent pricing |

**Tier 3 — Quality Band**

| Field | Condition | Rationale |
|-------|-----------|-----------|
| Rating | ± 0.5 stars | Higher-rated operators legitimately command a premium |
| Reviews | ≥ 50 | Filters out operators without sufficient credibility |

**Performance:** Uses a single vectorized pandas `merge` on Tier 1 keys instead of a Python loop — runs in ~3–5 minutes on 850k rows vs ~45 minutes with a loop.

---

### Task 2 — Price Flagging

A flag is raised only when **both** conditions are simultaneously breached:

```
|WAP Diff %| > threshold  AND  |WAP Diff ₹| > ₹75
```

The `₹75` absolute floor prevents flagging trivial differences on cheap buses.

**Dynamic Thresholds**

The base threshold of 15% widens based on two contextual signals:

| Signal | Condition | Adjustment | Logic |
|--------|-----------|------------|-------|
| Load Factor | > 80% occupancy | +10% on upper band | High demand justifies higher pricing |
| Load Factor | < 30% occupancy | +10% on lower band | Low occupancy — discounting may be intentional |
| SRP Rank | Top 20% on route/date | +5% on upper band | Visibility premium justifies modest price premium |

Adjustments stack — a top-20% ranked bus with 85% load gets an upper threshold of **30%** before being flagged.

**Severity**

Based on how far the deviation exceeds the threshold (not the raw deviation):

| Severity | Excess beyond threshold | Action |
|----------|------------------------|--------|
| CRITICAL | > 30% | Immediate review |
| HIGH | 15% – 30% | Pricing action recommended |
| MEDIUM | 5% – 15% | Review and consider adjustment |
| LOW | 0% – 5% | Monitor |

**Confidence**

| Level | Pool Size | Meaning |
|-------|-----------|---------|
| HIGH | ≥ 5 buses | Statistically reliable — act directly |
| MEDIUM | 3 – 4 buses | Directionally reliable — treat with caution |
| LOW | < 3 buses | Review manually before acting |

---

## Automation

### Local — Windows Task Scheduler

Create `run_pipeline.bat`:

```bat
cd C:\pricing_pipeline
python similarity.py && python flagging.py && python build_final_workbook.py
```

Point Task Scheduler to this file, set trigger to daily at 06:00.

### Local — Linux Cron

```bash
# crontab -e
0 6 * * * cd /opt/pricing_pipeline && python3 run_pipeline.py >> logs/pipeline.log 2>&1
```

### Cloud

| Platform | Trigger | Notes |
|----------|---------|-------|
| AWS Lambda + EventBridge | Scheduled rule | Serverless, output to S3 |
| GitHub Actions | Workflow cron | Free runner, output to SharePoint or S3 |
| Azure Functions | Timer trigger | Integrates with Power BI |

---

## Key Parameters

All similarity and flagging thresholds are defined as constants at the top of each script — easy to tune without touching logic:

```python
# similarity.py
DEP_WINDOW_MIN = 90    # ± minutes for departure time match
DUR_TOLERANCE  = 45    # ± minutes for journey duration match
MIN_REVIEWS    = 50    # minimum reviews for competitor credibility
RATING_WINDOW  = 0.5   # ± stars for quality band match

# flagging.py
BASE_PCT_THRESHOLD  = 15.0   # % deviation to trigger flag
BASE_ABS_THRESHOLD  = 75.0   # ₹ absolute deviation to trigger flag
LOAD_HIGH           = 0.80   # above this → high demand adjustment
LOAD_LOW            = 0.30   # below this → low demand adjustment
LOAD_ADJUSTMENT     = 10.0   # % added to threshold for load signal
RANK_ADJUSTMENT     = 5.0    # % added to upper threshold for top-20% rank
```

---

## Assumptions

| Assumption | Detail |
|------------|--------|
| Operator identity | Flixbus identified by operator name in `Operator` column |
| Boolean encoding | `Is AC`, `Is Seater`, `Is Sleeper` stored as `1.0 / NaN` floats from Excel |
| Departure Time format | Stored as `datetime.time` objects — converted to minutes since midnight |
| Load factor | No dedicated column — computed as `(Total Seats - Available Seats) / Total Seats` |
| Duplicate handling | Same bus appears multiple times across extraction snapshots — deduplicated before matching and before peer stats |
| Rating window | Set to ±0.5 after diagnostic analysis showed ±0.3 cut the comparable pool too aggressively on the real dataset |
| SRP rank top 20% | Computed per route per date from total listing count in SRP Rank string (e.g. `"17/165"` → top 20% = rank ≤ 33) |

---

## Diagnostics

If the Comparables sheet comes back empty, run the included diagnostic scripts to identify the issue:

```bash
python diagnose.py    # checks column formats, dtypes, sample values
python diagnose2.py   # tests merge at each Tier 1 key individually
python diagnose3.py   # traces how many rows survive each filter step
```

---

## AI Tool Usage

This project was developed with Claude (Anthropic) as a coding and structuring assistant. AI contributed to framework design, code generation, data diagnostics, and performance optimisation. All key decisions — field selection, threshold values, deduplication logic — were made by the analyst. AI served as a tool, not a decision-maker.

---

## License

For internal use only. Not for distribution.
