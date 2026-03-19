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

df['AC_Flag']     = df['Is AC'].apply(is_true)
df['Type_Cat']    = df.apply(bus_type_category, axis=1)
df['Product_Key'] = df['AC_Flag'].map({True: 'AC', False: 'NonAC'}) + '_' + df['Type_Cat']

flixbus_df = df[df['Operator'] == 'Flixbus'].copy()
comp_df    = df[df['Operator'] != 'Flixbus'].copy()

print("=== PRODUCT KEY samples (Flixbus) ===")
print(flixbus_df['Product_Key'].value_counts())

print("\n=== PRODUCT KEY samples (Competitors) ===")
print(comp_df['Product_Key'].value_counts().head(10))

print("\n=== ROUTE NUMBER unique (Flixbus) ===")
print(sorted(flixbus_df['Route Number'].unique())[:10])

print("\n=== ROUTE NUMBER unique (Competitors) ===")
print(sorted(comp_df['Route Number'].unique())[:10])

print("\n=== DEPARTURE DATE unique (Flixbus) ===")
print(flixbus_df['Departure Date'].unique()[:5])

print("\n=== DEPARTURE DATE unique (Competitors) ===")
print(comp_df['Departure Date'].unique()[:5])

# Try a minimal merge on just Route Number + Departure Date
test_merge = flixbus_df[['Route Number','Departure Date']].drop_duplicates().merge(
    comp_df[['Route Number','Departure Date']].drop_duplicates(),
    on=['Route Number','Departure Date'],
    how='inner'
)
print(f"\n=== Merge on Route + Date only: {len(test_merge)} matches ===")

# Try adding Product Key
test_merge2 = flixbus_df[['Route Number','Departure Date','Product_Key']].drop_duplicates().merge(
    comp_df[['Route Number','Departure Date','Product_Key']].drop_duplicates(),
    on=['Route Number','Departure Date','Product_Key'],
    how='inner'
)
print(f"=== Merge on Route + Date + Product Key: {len(test_merge2)} matches ===")
print(test_merge2.head(10))
