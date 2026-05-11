import pandas as pd
import numpy as np
import re

# --- CONFIGURATION ---
rwi_files = [
    ('apt_purchase', 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_APPURC_V16_PUF_YEAR_ABS.xlsx'),
    ('house_purchase', 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_HOUPURC_V16_PUF_YEAR_ABS.xlsx'), 
    ('renting', 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_APRENT_V16_PUF_YEAR_ABS.xlsx'),        
]

ecb_name_map = {
    'Deposit facility - date of changes (raw data) - Level (FM.D.U2.EUR.4F.KR.DFR.LEV)': 'Deposit_Facility',
    'Marginal lending facility - date of changes (raw data) - Level (FM.D.U2.EUR.4F.KR.MLFR.LEV)': 'Marginal_Lending',
    'Main refinancing operations - Minimum bid rate/fixed rate (date of changes) - Level (FM.D.U2.EUR.4F.KR.MRR_RT.LEV)': 'Main_Refinancing'
}

print("--- Step 1: Processing Inflation Data ---")
df_inflation = pd.read_csv('data/destatis_VPX_Inflation_de.csv', sep=';', skiprows=6, header=None)
df_inflation = df_inflation[[0, 3]].rename(columns={0: 'Year', 3: 'Inflation_YoY'})

# DEBUG: See what's at the end of the file before cleaning
print(f"Tail of raw inflation data:\n{df_inflation.tail(5)}")

# CLEANING: Keep only rows where 'Year' is exactly 4 digits
# This removes the "__________" footer rows causing your error
df_inflation['Year'] = df_inflation['Year'].astype(str).str.strip()
df_inflation = df_inflation[df_inflation['Year'].str.match(r'^\d{4}$', na=False)].copy()

print(f"Cleaned inflation years found: {df_inflation['Year'].unique()[:5]} ... {df_inflation['Year'].unique()[-5:]}")

df_inflation['Inflation_YoY'] = pd.to_numeric(df_inflation['Inflation_YoY'].astype(str).str.replace(',', '.'), errors='coerce')
df_inflation['DATE'] = pd.to_datetime(df_inflation['Year'] + '-01-01')
df_inflation = df_inflation.drop(columns=['Year'])

print("--- Step 2: Preparing ECB Data ---")
df_ecb = pd.read_csv('data/ecb_interest_rates_cleaned.csv')
df_ecb = df_ecb.rename(columns=ecb_name_map)
df_ecb['DATE'] = pd.to_datetime(df_ecb['DATE'])

start_year = df_ecb['DATE'].min().year
end_year = df_ecb['DATE'].max().year
jan_anchors = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-01-01', freq='YS')

df_final = pd.concat([df_ecb, pd.DataFrame({'DATE': jan_anchors})]).sort_values('DATE').drop_duplicates('DATE')

short_rate_cols = list(ecb_name_map.values())
df_final[short_rate_cols] = df_final[short_rate_cols].ffill()

print(f"ECB Skeleton prepared with {len(df_final)} rows.")

print("--- Step 3: Merging Inflation ---")
df_final = pd.merge(df_final, df_inflation, on='DATE', how='left')

print("--- Step 4: Merging RWI Data ---")
for suffix, filepath in rwi_files:
    try:
        sheet = "Distr_RegionEff_abs_yearly"
        df_rwi = pd.read_excel(filepath, sheet_name=sheet)
        row_data = df_rwi[df_rwi['kid2019'].astype(str).str.strip() == 'Weighted Mean']
        
        if not row_data.empty:
            pindex_cols = [c for c in row_data.columns if str(c).lower().startswith('pindex')]
            df_long = row_data[pindex_cols].melt(var_name='Year_Raw', value_name=f'pindex_{suffix}')
            
            df_long['Year'] = df_long['Year_Raw'].str.extract(r'(\d{4})')
            df_long = df_long.sort_values('Year')
            
            # Ensure Year is valid before converting to Date
            df_long = df_long[df_long['Year'].notna()].copy()
            df_long[f'pindex_{suffix}_YoY'] = df_long[f'pindex_{suffix}'].pct_change() * 100
            
            df_long['DATE'] = pd.to_datetime(df_long['Year'] + '-01-01')
            df_long = df_long.drop(columns=['Year_Raw', 'Year'])
            
            df_final = pd.merge(df_final, df_long, on='DATE', how='left')
            print(f"  [SUCCESS] {suffix}")
        else:
            print(f"  [SKIP] 'Weighted Mean' not found in {filepath}")
            
    except Exception as e:
        print(f"  [ERROR] {filepath}: {e}")

# --- Final Cleanup ---
if 'TIME PERIOD' in df_final.columns:
    df_final = df_final.drop(columns=['TIME PERIOD'])

cols_to_round = [c for c in df_final.columns if any(x in c for x in ['pindex', 'YoY', 'Facility'])]
df_final[cols_to_round] = df_final[cols_to_round].round(4)

print("\n--- Final Preview ---")
print(df_final.head(5))

df_final.to_csv('ecb_inflation_rwi_master.csv', index=False)
print("\nProcess finished. File saved as 'ecb_inflation_rwi_master.csv'")