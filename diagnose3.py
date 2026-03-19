import pandas as pd

df = pd.read_excel('dataset.xlsx')

def is_true(val):
    try:
        return float(val) == 1.0
    except:
        return False

def bus_type_category(row):
    seater  = is_true(row['Is Seater'])
    sleeper = is_true(row['Is Sleeper'])
    if seater and sleeper:  return 'Mixed'
    elif sleeper:           return 'Sleeper'
    elif seater:            return 'Seater'
    return 'Unknown'

def time_to_min(t):
    try:
        h, m = map(int, str(t).strip().split(':'))
        return h * 60 + m
    except:
        return None

df['AC_Flag']     = df['Is AC'].apply(is_true)
df['Type_Cat']    = df.apply(bus_type_category, axis=1)
df['Product_Key'] = df['AC_Flag'].map({True: 'AC', False: 'NonAC'}) + '_' + df['Type_Cat']
df['Dep_Min']     = df['Departure Time'].apply(time_to_min)
df['WAP']         = pd.to_numeric(df['Weighted Average Price'], errors='coerce')
df['Rating']      = pd.to_numeric(df['Total Ratings'],          errors='coerce')
df['Reviews']     = pd.to_numeric(df['Number of Reviews'],      errors='coerce')
df['Duration']    = pd.to_numeric(df['Journey Duration (Min)'], errors='coerce')

flixbus_df = df[df['Operator'] == 'Flixbus'].copy()
comp_df    = df[df['Operator'] != 'Flixbus'].copy()

print("=== DEPARTURE TIME raw samples (Flixbus) ===")
print(flixbus_df['Departure Time'].head(10).tolist())

print("\n=== DEPARTURE TIME raw samples (Competitors) ===")
print(comp_df['Departure Time'].head(10).tolist())

print("\n=== DEP_MIN nulls (Flixbus)     :", flixbus_df['Dep_Min'].isna().sum(), "of", len(flixbus_df))
print("=== DEP_MIN nulls (Competitors) :", comp_df['Dep_Min'].isna().sum(), "of", len(comp_df))

print("\n=== DURATION nulls (Flixbus)     :", flixbus_df['Duration'].isna().sum())
print("=== DURATION nulls (Competitors) :", comp_df['Duration'].isna().sum())

print("\n=== RATING nulls (Flixbus)     :", flixbus_df['Rating'].isna().sum())
print("=== RATING nulls (Competitors) :", comp_df['Rating'].isna().sum())

print("\n=== REVIEWS nulls (Competitors) :", comp_df['Reviews'].isna().sum())
print("=== Competitors with reviews >= 50 :", (comp_df['Reviews'] >= 50).sum())

# Do the merge and check how many rows survive each filter individually
comp_df = comp_df[comp_df['Reviews'] >= 50].copy()

flix_slim = flixbus_df[['Route Number','Departure Date','Product_Key','Dep_Min','Duration','Rating']].rename(
    columns={'Product_Key':'Flixbus Product','Dep_Min':'Flixbus Dep_Min',
             'Duration':'Flixbus Duration','Rating':'Flixbus Rating'})

comp_slim = comp_df[['Route Number','Departure Date','Product_Key','Dep_Min','Duration','Rating']].rename(
    columns={'Product_Key':'Comp Product','Dep_Min':'Comp_Dep_Min',
             'Duration':'Comp Duration','Rating':'Comp Rating'})

merged = flix_slim.merge(comp_slim,
    left_on =['Route Number','Departure Date','Flixbus Product'],
    right_on=['Route Number','Departure Date','Comp Product'],
    how='inner')

print(f"\n=== After Tier 1 merge         : {len(merged)} rows ===")

merged['dep_delta'] = (merged['Flixbus Dep_Min'] - merged['Comp_Dep_Min']).abs()
merged['dur_delta'] = (merged['Flixbus Duration'] - merged['Comp Duration']).abs()
merged['rat_delta'] = (merged['Flixbus Rating']   - merged['Comp Rating']).abs()

t2a = merged[merged['dep_delta'] <= 90]
print(f"=== After dep time filter (±90): {len(t2a)} rows ===")

t2b = t2a[t2a['dur_delta'] <= 45]
print(f"=== After duration filter (±45): {len(t2b)} rows ===")

t3  = t2b[t2b['rat_delta'] <= 0.3]
print(f"=== After rating filter (±0.3) : {len(t3)} rows ===")

print("\n=== Sample dep_delta values ===")
print(merged['dep_delta'].describe())

print("\n=== Sample dur_delta values ===")
print(merged['dur_delta'].describe())

print("\n=== Sample rat_delta values ===")
print(merged['rat_delta'].describe())
