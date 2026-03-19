import pandas as pd

# ── 1. LOAD DATA ───────────────────────────────────────────────────────────────
df = pd.read_excel('dataset.xlsx')

# ── 2. PARSE & DERIVE FIELDS ───────────────────────────────────────────────────

df['SRP_Rank_Num'] = df['SRP Rank'].str.extract(r'(\d+)/').astype(int)

# Departure Time comes in as datetime.time objects from Excel
def time_to_min(t):
    try:
        return t.hour * 60 + t.minute
    except AttributeError:
        try:
            # fallback: handle "HH:MM" or "HH:MM:SS" strings
            parts = str(t).strip().split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return None

df['Dep_Min'] = df['Departure Time'].apply(time_to_min)

# Is AC / Is Seater / Is Sleeper come in as 1.0 / nan
def is_true(val):
    try:
        return float(val) == 1.0
    except:
        return False

df['AC_Flag'] = df['Is AC'].apply(is_true)

def bus_type_category(row):
    seater  = is_true(row['Is Seater'])
    sleeper = is_true(row['Is Sleeper'])
    if seater and sleeper:  return 'Mixed'
    elif sleeper:           return 'Sleeper'
    elif seater:            return 'Seater'
    return 'Unknown'

df['Type_Cat']    = df.apply(bus_type_category, axis=1)
df['Product_Key'] = df['AC_Flag'].map({True: 'AC', False: 'NonAC'}) + '_' + df['Type_Cat']

df['WAP']      = pd.to_numeric(df['Weighted Average Price'],  errors='coerce')
df['Rating']   = pd.to_numeric(df['Total Ratings'],           errors='coerce')
df['Reviews']  = pd.to_numeric(df['Number of Reviews'],       errors='coerce')
df['Duration'] = pd.to_numeric(df['Journey Duration (Min)'],  errors='coerce')

# ── 3. SIMILARITY PARAMETERS ──────────────────────────────────────────────────
DEP_WINDOW_MIN = 90    # ±90 minutes
DUR_TOLERANCE  = 45    # ±45 minutes
MIN_REVIEWS    = 50    # minimum reviews
RATING_WINDOW  = 0.5   # ±0.5 stars (widened — real data rating deltas are larger)

# ── 4. SPLIT FLIXBUS vs COMPETITORS ───────────────────────────────────────────
flixbus_df = df[df['Operator'] == 'Flixbus'].copy()
comp_df    = df[df['Operator'] != 'Flixbus'].copy()

# Pre-filter competitors on Tier 3 quality band (static — do once)
comp_df = comp_df[comp_df['Reviews'] >= MIN_REVIEWS].copy()

# Deduplicate — same operator on same route/date/departure can appear multiple
# times across extraction snapshots; keep the highest-ranked (lowest rank number) entry
comp_df = (
    comp_df
    .sort_values('SRP_Rank_Num')
    .drop_duplicates(subset=['Operator', 'Route Number', 'Departure Date', 'Departure Time'])
    .copy()
)

# ── 5. VECTORIZED MERGE ───────────────────────────────────────────────────────
flix_slim = flixbus_df[[
    'Route Number', 'Departure Date',
    'SRP_Rank_Num', 'Departure Time', 'Product_Key', 'Bus Type',
    'WAP', 'Rating', 'Reviews', 'Dep_Min', 'Duration'
]].rename(columns={
    'SRP_Rank_Num'  : 'Flixbus SRP Rank',
    'Departure Time': 'Flixbus Departure Time',
    'Product_Key'   : 'Flixbus Product',
    'Bus Type'      : 'Flixbus Bus Type',
    'WAP'           : 'Flixbus WAP',
    'Rating'        : 'Flixbus Rating',
    'Reviews'       : 'Flixbus Reviews',
    'Dep_Min'       : 'Flixbus Dep_Min',
    'Duration'      : 'Flixbus Duration',
})

comp_slim = comp_df[[
    'Route Number', 'Departure Date', 'Operator', 'Bus Type',
    'Product_Key', 'SRP_Rank_Num', 'Departure Time',
    'Duration', 'Rating', 'Reviews', 'WAP', 'Dep_Min'
]].rename(columns={
    'SRP_Rank_Num'  : 'Competitor SRP Rank',
    'Departure Time': 'Competitor Departure Time',
    'Duration'      : 'Competitor Duration (Min)',
    'Rating'        : 'Competitor Rating',
    'Reviews'       : 'Competitor Reviews',
    'WAP'           : 'Competitor WAP',
    'Dep_Min'       : 'Comp_Dep_Min',
    'Bus Type'      : 'Competitor Bus Type',
    'Product_Key'   : 'Competitor Product Key',
})

# Merge on Tier 1 hard filters
merged = flix_slim.merge(
    comp_slim,
    left_on =['Route Number', 'Departure Date', 'Flixbus Product'],
    right_on=['Route Number', 'Departure Date', 'Competitor Product Key'],
    how='inner'
)

# Apply Tier 2 + Tier 3 filters vectorized
merged['Dep Time Delta (Min)'] = (merged['Flixbus Dep_Min'] - merged['Comp_Dep_Min']).abs()
merged['Duration Delta (Min)'] = (merged['Flixbus Duration'] - merged['Competitor Duration (Min)']).abs()
merged['Rating Delta']         = (merged['Flixbus Rating']   - merged['Competitor Rating']).abs().round(2)

comparable_df = merged[
    (merged['Dep Time Delta (Min)'] <= DEP_WINDOW_MIN) &
    (merged['Duration Delta (Min)'] <= DUR_TOLERANCE)  &
    (merged['Rating Delta']         <= RATING_WINDOW)
].copy()

comparable_df.drop(columns=['Flixbus Dep_Min', 'Flixbus Duration',
                             'Comp_Dep_Min', 'Competitor Product Key'], inplace=True)

# ── 6. SUMMARY — one row per Flixbus listing ──────────────────────────────────
peer_stats = (
    comparable_df
    .groupby(['Route Number', 'Departure Date', 'Flixbus Departure Time', 'Flixbus Product'])
    ['Competitor WAP']
    .agg(
        Comparable_Pool_Size='count',
        Peer_Median_WAP='median',
        Peer_Mean_WAP='mean',
        Peer_Min_WAP='min',
        Peer_Max_WAP='max',
    )
    .reset_index()
)

summary_df = flix_slim.merge(
    peer_stats,
    on=['Route Number', 'Departure Date', 'Flixbus Departure Time', 'Flixbus Product'],
    how='left'
)

summary_df['Comparable Pool Size'] = summary_df['Comparable_Pool_Size'].fillna(0).astype(int)
summary_df['Peer Median WAP']      = summary_df['Peer_Median_WAP'].round(2)
summary_df['Peer Mean WAP']        = summary_df['Peer_Mean_WAP'].round(2)
summary_df['Peer Min WAP']         = summary_df['Peer_Min_WAP']
summary_df['Peer Max WAP']         = summary_df['Peer_Max_WAP']
summary_df['WAP Diff vs Median']   = (summary_df['Flixbus WAP'] - summary_df['Peer Median WAP']).round(2)
summary_df['WAP Diff % vs Median'] = (
    summary_df['WAP Diff vs Median'] / summary_df['Peer Median WAP'] * 100
).round(1)

summary_df.drop(columns=[
    'Comparable_Pool_Size', 'Peer_Median_WAP', 'Peer_Mean_WAP',
    'Peer_Min_WAP', 'Peer_Max_WAP', 'Flixbus Dep_Min', 'Flixbus Duration'
], inplace=True)

# ── 7. WRITE TO EXCEL ─────────────────────────────────────────────────────────
output_file = 'similarity_output.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    summary_df.to_excel(writer,    sheet_name='Summary',     index=False)
    comparable_df.to_excel(writer, sheet_name='Comparables', index=False)

    for sheet_name in ['Summary', 'Comparables']:
        ws = writer.sheets[sheet_name]
        for col in ws.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)