import pandas as pd

# 1. Load the dataset
# Replace 'ecb_rates.csv' with your actual filename
df = pd.read_csv('data/ECB Data Portal_20260511095310.csv')

# 2. Define the interest rate columns to monitor for changes
# We exclude DATE and TIME PERIOD
rate_columns = [
    'Deposit facility - date of changes (raw data) - Level (FM.D.U2.EUR.4F.KR.DFR.LEV)',
    'Marginal lending facility - date of changes (raw data) - Level (FM.D.U2.EUR.4F.KR.MLFR.LEV)',
    'Main refinancing operations - Minimum bid rate/fixed rate (date of changes) - Level (FM.D.U2.EUR.4F.KR.MRR_RT.LEV)'
]

# 3. Create a mask to identify changes
# .ne() checks if the value is "Not Equal" to the previous row (.shift())
# .any(axis=1) keeps the row if at least ONE of the columns changed
changes_mask = df[rate_columns].ne(df[rate_columns].shift()).any(axis=1)

# 4. Apply the filter
# Note: The first row is always kept because shift() compares it to NaN
df_cleaned = df[changes_mask]

# 5. Save the cleaned version
df_cleaned.to_csv('data/ecb_interest_rates_cleaned.csv', index=False)

print(f"Processing complete. Kept {len(df_cleaned)} rows out of {len(df)}.")