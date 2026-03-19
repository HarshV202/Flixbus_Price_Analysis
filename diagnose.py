import pandas as pd

df = pd.read_excel('dataset.xlsx')

# ── Check join key values ──────────────────────────────────────────────────────
flixbus_df = df[df['Operator'] == 'Flixbus'].copy()
comp_df    = df[df['Operator'] != 'Flixbus'].copy()

print("=== FLIXBUS ROW COUNT ===")
print(len(flixbus_df))

print("\n=== SAMPLE Departure Date values (Flixbus) ===")
print(flixbus_df['Departure Date'].head(5).tolist())

print("\n=== SAMPLE Departure Date values (Competitors) ===")
print(comp_df['Departure Date'].head(5).tolist())

print("\n=== Departure Date dtypes ===")
print("Flixbus   :", flixbus_df['Departure Date'].dtype)
print("Competitor:", comp_df['Departure Date'].dtype)

print("\n=== SAMPLE Is AC values (Flixbus) ===")
print(flixbus_df['Is AC'].head(5).tolist())

print("\n=== SAMPLE Is AC values (Competitors) ===")
print(comp_df['Is AC'].head(5).tolist())

print("\n=== SAMPLE Is Seater values ===")
print(comp_df['Is Seater'].head(5).tolist())

print("\n=== SAMPLE Is Sleeper values ===")
print(comp_df['Is Sleeper'].head(5).tolist())

print("\n=== SAMPLE Route Number values (Flixbus) ===")
print(flixbus_df['Route Number'].head(5).tolist())

print("\n=== SAMPLE Route Number values (Competitors) ===")
print(comp_df['Route Number'].head(5).tolist())

print("\n=== Route Number dtypes ===")
print("Flixbus   :", flixbus_df['Route Number'].dtype)
print("Competitor:", comp_df['Route Number'].dtype)
