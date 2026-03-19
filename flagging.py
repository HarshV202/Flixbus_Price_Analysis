import pandas as pd

# ── 1. LOAD SIMILARITY OUTPUT ──────────────────────────────────────────────────
summary = pd.read_excel('similarity_output.xlsx', sheet_name='Summary')

# ── 2. LOAD ORIGINAL DATASET FOR LOAD + RANK CONTEXT ─────────────────────────
df = pd.read_excel('dataset.xlsx')

def is_true(val):
    try:
        return float(val) == 1.0
    except:
        return False

df['Available Seats'] = pd.to_numeric(df['Available Seats'], errors='coerce')
df['Total Seats']     = pd.to_numeric(df['Total Seats'],     errors='coerce')
df['Load Factor']     = (df['Total Seats'] - df['Available Seats']) / df['Total Seats']
df['SRP_Rank_Num']    = df['SRP Rank'].str.extract(r'(\d+)/(\d+)').astype(float).apply(
    lambda r: r[0], axis=1
)
df['Total_Listings']  = df['SRP Rank'].str.extract(r'(\d+)/(\d+)').astype(float).apply(
    lambda r: r[1], axis=1
)

# Keep only Flixbus rows with the fields we need
flix_context = df[df['Operator'] == 'Flixbus'][[
    'Route Number', 'Departure Date', 'SRP Rank',
    'Departure Time', 'Available Seats', 'Total Seats',
    'Load Factor', 'SRP_Rank_Num', 'Total_Listings'
]].copy()

# Deduplicate — keep one row per Flixbus listing (same route/date/departure)
flix_context = (
    flix_context
    .sort_values('SRP_Rank_Num')
    .drop_duplicates(subset=['Route Number', 'Departure Date', 'Departure Time'])
    .copy()
)

# Departure Date as datetime to match summary sheet
flix_context['Departure Date'] = pd.to_datetime(flix_context['Departure Date'], errors='coerce')

# ── 3. MERGE CONTEXT INTO SUMMARY ─────────────────────────────────────────────
summary['Departure Date'] = pd.to_datetime(summary['Departure Date'], errors='coerce')

# Departure Time: normalise to string HH:MM for join
def norm_time(t):
    try:
        return f"{t.hour:02d}:{t.minute:02d}"
    except:
        return str(t)[:5]

summary['Dep_Time_Key']      = summary['Flixbus Departure Time'].apply(norm_time)
flix_context['Dep_Time_Key'] = flix_context['Departure Time'].apply(norm_time)

merged = summary.merge(
    flix_context[['Route Number', 'Departure Date', 'Dep_Time_Key',
                  'Load Factor', 'SRP_Rank_Num', 'Total_Listings',
                  'Available Seats', 'Total Seats']],
    on=['Route Number', 'Departure Date', 'Dep_Time_Key'],
    how='left'
)

# ── 4. COMPUTE TOP-20% RANK THRESHOLD PER ROUTE + DATE ────────────────────────
rank_threshold = (
    merged.groupby(['Route Number', 'Departure Date'])['Total_Listings']
    .first()
    .mul(0.20)
    .reset_index()
    .rename(columns={'Total_Listings': 'Top20_Threshold'})
)
merged = merged.merge(rank_threshold, on=['Route Number', 'Departure Date'], how='left')
merged['Is_Top20_Rank'] = merged['SRP_Rank_Num'] <= merged['Top20_Threshold']

# ── 5. FLAGGING PARAMETERS ────────────────────────────────────────────────────
BASE_PCT_THRESHOLD  = 15.0   # % deviation to trigger flag
BASE_ABS_THRESHOLD  = 75.0   # ₹ absolute deviation to trigger flag
LOAD_HIGH           = 0.80   # above this → high demand, widen upper band
LOAD_LOW            = 0.30   # below this → low demand, widen lower band
LOAD_ADJUSTMENT     = 10.0   # extra % allowance for load context
RANK_ADJUSTMENT     = 5.0    # extra % allowance for top-20% rank
MIN_POOL_HIGH_CONF  = 5      # pool size for high confidence
MIN_POOL_MED_CONF   = 3      # pool size for medium confidence

# ── 6. FLAGGING LOGIC ─────────────────────────────────────────────────────────
def compute_flag(row):
    wap_diff_pct = row['WAP Diff % vs Median']
    wap_diff_abs = row['WAP Diff vs Median']
    load         = row['Load Factor']
    is_top20     = row['Is_Top20_Rank']
    pool_size    = row['Comparable Pool Size']
    peer_median  = row['Peer Median WAP']

    # No comparables — cannot flag
    if pd.isna(peer_median) or pool_size == 0:
        return pd.Series({
            'Flag'              : 'NO COMPARABLES',
            'Flag Direction'    : None,
            'Flag Severity'     : None,
            'Confidence'        : None,
            'Upper Threshold %' : None,
            'Lower Threshold %' : None,
            'Load Factor'       : load,
            'Is Top 20% Rank'   : is_top20,
        })

    # Confidence based on pool size
    if pool_size >= MIN_POOL_HIGH_CONF:
        confidence = 'HIGH'
    elif pool_size >= MIN_POOL_MED_CONF:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'

    # Dynamic thresholds
    upper_threshold = BASE_PCT_THRESHOLD
    lower_threshold = BASE_PCT_THRESHOLD

    # Load adjustment
    if pd.notna(load):
        if load > LOAD_HIGH:
            upper_threshold += LOAD_ADJUSTMENT   # high demand — allow higher price
        elif load < LOAD_LOW:
            lower_threshold += LOAD_ADJUSTMENT   # low demand — flag underpricing less aggressively

    # Rank adjustment — top 20% rank gets wider upper band
    if is_top20:
        upper_threshold += RANK_ADJUSTMENT

    # Flag decision — BOTH % and absolute thresholds must be breached
    if wap_diff_pct > upper_threshold and wap_diff_abs > BASE_ABS_THRESHOLD:
        direction = 'TOO HIGH'
        excess    = wap_diff_pct - upper_threshold
    elif wap_diff_pct < -lower_threshold and wap_diff_abs < -BASE_ABS_THRESHOLD:
        direction = 'TOO LOW'
        excess    = abs(wap_diff_pct) - lower_threshold
    else:
        return pd.Series({
            'Flag'              : 'OK',
            'Flag Direction'    : None,
            'Flag Severity'     : None,
            'Confidence'        : confidence,
            'Upper Threshold %' : upper_threshold,
            'Lower Threshold %' : lower_threshold,
            'Load Factor'       : round(load, 3) if pd.notna(load) else None,
            'Is Top 20% Rank'   : is_top20,
        })

    # Severity based on how far beyond threshold
    if excess > 30:
        severity = 'CRITICAL'
    elif excess > 15:
        severity = 'HIGH'
    elif excess > 5:
        severity = 'MEDIUM'
    else:
        severity = 'LOW'

    return pd.Series({
        'Flag'              : 'FLAGGED',
        'Flag Direction'    : direction,
        'Flag Severity'     : severity,
        'Confidence'        : confidence,
        'Upper Threshold %' : upper_threshold,
        'Lower Threshold %' : lower_threshold,
        'Load Factor'       : round(load, 3) if pd.notna(load) else None,
        'Is Top 20% Rank'   : is_top20,
    })

flag_cols = merged.apply(compute_flag, axis=1)
output    = pd.concat([merged, flag_cols], axis=1)

# ── 7. CLEAN UP OUTPUT COLUMNS ────────────────────────────────────────────────
output.drop(columns=['Dep_Time_Key', 'Top20_Threshold', 'SRP_Rank_Num',
                     'Total_Listings', 'Available Seats', 'Total Seats'],
            inplace=True, errors='ignore')

# Reorder: flag columns right after WAP diff
base_cols = [
    'Route Number', 'Departure Date', 'Flixbus SRP Rank',
    'Flixbus Departure Time', 'Flixbus Product', 'Flixbus Bus Type',
    'Flixbus WAP', 'Flixbus Rating', 'Flixbus Reviews',
    'Comparable Pool Size', 'Peer Median WAP', 'Peer Mean WAP',
    'Peer Min WAP', 'Peer Max WAP',
    'WAP Diff vs Median', 'WAP Diff % vs Median',
    'Flag', 'Flag Direction', 'Flag Severity', 'Confidence',
    'Upper Threshold %', 'Lower Threshold %',
    'Load Factor', 'Is Top 20% Rank',
]
output = output[[c for c in base_cols if c in output.columns]]

# ── 8. SUMMARY STATS SHEET ────────────────────────────────────────────────────
flagged     = output[output['Flag'] == 'FLAGGED']
flag_counts = flagged.groupby(['Flag Direction', 'Flag Severity']).size().reset_index(name='Count')

stats = pd.DataFrame({
    'Metric': [
        'Total Flixbus listings',
        'Listings with comparables',
        'Listings flagged',
        'Flagged TOO HIGH',
        'Flagged TOO LOW',
        'Flag rate (%)',
    ],
    'Value': [
        len(output),
        int((output['Flag'] != 'NO COMPARABLES').sum()),
        len(flagged),
        int((flagged['Flag Direction'] == 'TOO HIGH').sum()),
        int((flagged['Flag Direction'] == 'TOO LOW').sum()),
        round(len(flagged) / (output['Flag'] != 'NO COMPARABLES').sum() * 100, 1),
    ]
})

# ── 9. WRITE TO EXCEL ─────────────────────────────────────────────────────────
output_file = 'flagging_output.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    output.to_excel(writer,      sheet_name='Flagging Output', index=False)
    stats.to_excel(writer,       sheet_name='Stats',           index=False)
    flag_counts.to_excel(writer, sheet_name='Flag Breakdown',  index=False)

    for sheet_name in ['Flagging Output', 'Stats', 'Flag Breakdown']:
        ws = writer.sheets[sheet_name]
        for col in ws.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)