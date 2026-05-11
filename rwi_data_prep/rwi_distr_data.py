import pandas as pd
import numpy as np

# 1. Configuration
rwi_files = {
    'apt_purchase': 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_APPURC_V16_PUF_YEAR_ABS.xlsx',
    'house_purchase': 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_HOUPURC_V16_PUF_YEAR_ABS.xlsx',
    'renting': 'data/RWI-GEO-REDX_PUF_V16/RWIGEOREDX_APRENT_V16_PUF_YEAR_ABS.xlsx'
}

sheet = "Distr_RegionEff_abs_yearly"

for category, path in rwi_files.items():
    print(f"Processing and formatting: {category}...")
    
    try:
        df = pd.read_excel(path, sheet_name=sheet)
    except Exception as e:
        print(f"Could not load {category}: {e}")
        continue

    # 2. Identify and Clean Columns
    pindex_cols = [col for col in df.columns if col.startswith('pindex')]
    nobs_cols = [col for col in df.columns if col.startswith('NOBS')]
    
    # Drop non-numerical "means" rows by coercing pindex to numeric
    df[pindex_cols] = df[pindex_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=pindex_cols).copy()

    # 3. Apply Formatting to Original Data
    # Round pindex to 3 decimal places
    df[pindex_cols] = df[pindex_cols].round(3)
    
    # Convert NOBS to integers (ensure no NaNs remain first)
    df[nobs_cols] = df[nobs_cols].fillna(0).astype(int)

    # 4. Calculate YoY Returns (as percentages)
    # Scale by 100 and round to 2 decimal places
    yoy_df = (df[pindex_cols].pct_change(axis=1) * 100).round(4)
    
    # Rename and clean up return columns
    return_cols = [f"return_{col[-4:]}" for col in pindex_cols]
    yoy_df.columns = return_cols
    valid_return_cols = return_cols[1:] # Drop first year (NaN)
    yoy_df = yoy_df[valid_return_cols]

    # 5. Calculate Average Metrics
    # These will already be in percentage format (rounded to 2)
    df['avg_return_all_time'] = yoy_df.mean(axis=1).round(2)
    df['avg_return_10yr'] = yoy_df[valid_return_cols[-10:]].mean(axis=1).round(2)
    df['avg_return_5yr'] = yoy_df[valid_return_cols[-5:]].mean(axis=1).round(2)

    # 6. Final Assembly
    # Combine original df with the new return columns
    final_df = pd.concat([df, yoy_df], axis=1)
    final_df['dataset_type'] = category

    # 7. Export
    output_filename = f"{category}_full_processed_data.csv"
    final_df.to_csv(output_filename, index=False)
    
    print(f"Saved: {output_filename} ({len(final_df)} rows)")

print("\nProcessing complete! Your files are now formatted and scaled.")