# Flixbus_Price_Analysis
📌 Overview

This project analyzes how Flixbus is priced relative to competitors and identifies pricing inefficiencies using a data-driven approach.

It combines:

Similar bus matching

Price benchmarking (WAP)

Intelligent price flagging

Automated reporting pipeline

🎯 Objective

Identify comparable buses for each listing

Benchmark prices against competitors

Detect overpriced and underpriced listings

Provide actionable insights for pricing optimization

📂 Dataset

~850,000+ rows

Multi-route, multi-date bus listings

Key Features:

Price (WAP)

Route & Date

Departure Time & Duration

Bus Type (AC / Sleeper / Seater)

Ratings & Reviews

Seat Availability (Load Factor)

Search Ranking Position (SRP)

🧠 Approach
🔍 Similar Bus Matching

3-tier framework:

Hard Filters: Route, Date, Product Type

Soft Filters: Time (±90 mins), Duration (±45 mins)

Quality Filters: Rating (±0.5), Reviews ≥ 50

💰 Price Benchmarking

Uses Weighted Average Price (WAP)

Computes peer median price for comparison

🚨 Price Flagging

A listing is flagged only if:

Deviation > 15%

AND difference > ₹75

⚙️ Dynamic Adjustments

High demand (load) → allows higher pricing

Top SRP rank → allows premium pricing

📊 Severity Levels

CRITICAL → Immediate action

HIGH → Strong mispricing

MEDIUM → Moderate deviation

LOW → Minor variation

⚙️ Pipeline
Data → Preprocessing → Similarity Matching → Flagging → Report Generation

Fully automated

Runs in ~3–5 minutes

Handles 850k+ rows efficiently

🛠 Tech Stack

Python

pandas

openpyxl

📊 Key Results

~79% listings matched with comparables

53.6% listings flagged

Underpricing is 2× more frequent than overpricing

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
🚀 Future Improvements

Cloud deployment (AWS / GCP)

Database integration (PostgreSQL)

Dashboard (Power BI / Streamlit)

👨‍💻 Author

Harsh Verma
NSUT Delhi | Data Analyst Aspirant
