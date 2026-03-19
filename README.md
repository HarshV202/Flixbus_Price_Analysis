# Flixbus_Price_Analysis
A data-driven pricing analysis system that compares Flixbus listings with similar competitors using a multi-tier matching framework. It benchmarks prices with Weighted Average Price (WAP), flags mispriced listings using dynamic thresholds based on demand and visibility, and automates the pipeline to generate actionable insights at scale.
🚌 Bus Pricing Analysis & Automation System
📌 Overview

This project analyzes bus listing data to evaluate how Flixbus is priced relative to competitors and identifies pricing inefficiencies using a data-driven approach.

It combines:

Similarity-based competitor matching

Statistical price benchmarking

Dynamic pricing flagging

End-to-end automation pipeline

🎯 Objective

To build a system that:

Identifies comparable buses for each Flixbus listing

Benchmarks prices using market data

Flags overpriced and underpriced listings

Generates actionable insights for pricing optimization

📂 Dataset

~850,000+ rows of bus listings

Multi-route and multi-date data

Key Features:

Price (Weighted Average Price - WAP)

Route & Departure Date

Departure Time & Duration

Bus Type (AC / Sleeper / Seater)

Ratings & Reviews

Seat Availability (Load Factor)

Search Ranking Position (SRP)

🧠 Approach
1. Similar Bus Matching

A 3-tier filtering framework ensures only relevant competitors are selected:

Tier 1 (Hard Filters):

Route

Date

Product Type (AC + Bus Type)

Tier 2 (Soft Filters):

Departure Time (±90 mins)

Duration (±45 mins)

Tier 3 (Quality Filters):

Rating (±0.5)

Minimum 50 reviews

2. Price Benchmarking

Uses Weighted Average Price (WAP) instead of min/max price

Calculates peer median price for each listing

3. Price Flagging Logic

A listing is flagged only if:

Deviation > 15%

AND difference > ₹75

This avoids noise and ensures meaningful flags.

4. Dynamic Adjustments

Thresholds adapt based on:

Load Factor (Demand)

High load → allows higher price

Low load → allows lower price

Search Ranking (Visibility)

Top-ranked buses can justify premium pricing

5. Severity Levels
Severity	Description
CRITICAL	Immediate action required
HIGH	Strong mispricing
MEDIUM	Moderate deviation
LOW	Minor variation
6. Confidence Levels
Confidence	Comparable Count
HIGH	≥ 5
MEDIUM	3–4
LOW	< 3
⚙️ Pipeline Architecture
Daily Dataset → Data Preparation → Similarity Matching → Price Flagging → Report Generation
Steps:

Data ingestion (Excel input)

Feature engineering (time, load, product key)

Vectorized similarity matching (pandas)

Price flagging with dynamic thresholds

Excel report generation

⏱ Runtime: ~3–5 minutes for 850k+ rows

🛠 Tech Stack

Python 3

pandas (data processing)

openpyxl (Excel reporting)

📊 Key Results

~79% listings had valid comparables

53.6% listings flagged

Underpricing is 2× more frequent than overpricing

Multiple critical pricing gaps identified

🚀 Performance Optimization

Replaced row-by-row loops with vectorized pandas merge

Reduced runtime from ~60 mins → ~5 mins

📁 Project Structure
├── data/
│   └── dataset.xlsx
├── src/
│   ├── similarity.py
│   ├── flagging.py
│   ├── run_pipeline.py
│   └── build_final_workbook.py
├── output/
│   └── pricing_analysis_final.xlsx
├── README.md
🔄 Automation

Fully automated pipeline

Can be scheduled via cron / task scheduler

Optional integrations:

Email alerts

Slack notifications

🔮 Future Improvements

Deploy on cloud (AWS / GCP)

Store data in PostgreSQL / Data Warehouse

Build dashboard (Power BI / Streamlit)

Real-time pricing recommendations

👨‍💻 Author

Harsh Verma
Mechanical Engineering, NSUT Delhi
Aspiring Data Analyst
