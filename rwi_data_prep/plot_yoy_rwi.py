import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the "sparse" dataset
df = pd.read_csv('exports/rwi_geox_redx_exports/RWI_INF_ECB_yearly.csv')
df['DATE'] = pd.to_datetime(df['DATE'])

# --- FIGURE 1: Percentages ---
plt.figure(figsize=(14, 7))

# Interest rates are NOT sparse (we forward-filled them), so they plot normally
plt.step(df['DATE'], df['Marginal_Lending'], where='post', label='ECB Deposit Facility', alpha=0.5)
#plt.step(df['DATE'], df['Main_Refinancing'], where='post', label='ECB Main Refinancing', linewidth=2, color='navy')

# --- THE FIX FOR INFLATION ---
# We drop NaNs JUST for this line so the plot can connect the Jan 1st points
df_inf_plot = df.dropna(subset=['Inflation_YoY'])
plt.plot(df_inf_plot['DATE'], df_inf_plot['Inflation_YoY'], 
         label='CPI Inflation (Annual)', color='black', linewidth=2.5, marker='o', markersize=4)

# Repeat the fix for RWI YoY indices if they exist
for yoy_col in [c for c in df.columns if '_YoY' in c and 'Inflation' not in c]:
    df_yoy_plot = df.dropna(subset=[yoy_col])
    plt.plot(df_yoy_plot['DATE'], df_yoy_plot[yoy_col], 
             label=yoy_col.replace('pindex_', '').replace('_YoY', ' Growth'), 
             linestyle='--', marker='s', markersize=3, alpha=0.8)

plt.xlim(pd.Timestamp('2009-01-01'), pd.Timestamp('2025-1-1'))
plt.title('Macro Trends (2008-2025): ECB vs. Annual Indices', fontsize=14)
plt.ylabel('Percentage (%)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# --- FIGURE 2: Absolute Price Indices (Dual Y-Axis) ---
fig, ax1 = plt.subplots(figsize=(12, 6))

# Set the X-limit for the whole figure
plt.xlim(pd.Timestamp('2009-01-01'), pd.Timestamp('2025-1-1'))

# --- LEFT AXIS: Purchase Prices (Apt & House) ---
if 'pindex_apt_purchase' in df.columns:
    df_apt = df.dropna(subset=['pindex_apt_purchase'])
    ax1.plot(df_apt['DATE'], df_apt['pindex_apt_purchase'], 
             label='Apt Purchase Index', color='steelblue', linewidth=2, marker='o', markersize=4)

if 'pindex_house_purchase' in df.columns:
    df_house = df.dropna(subset=['pindex_house_purchase'])
    ax1.plot(df_house['DATE'], df_house['pindex_house_purchase'], 
             label='House Purchase Index', color='darkorange', linewidth=2, marker='s', markersize=4)

ax1.set_xlabel('Year')
ax1.set_ylabel('Purchase Price Index (€/sqm)', color='steelblue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='steelblue')
ax1.grid(True, alpha=0.3)

# --- RIGHT AXIS: Renting Index ---
if 'pindex_renting' in df.columns:
    ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis
    df_rent = df.dropna(subset=['pindex_renting'])
    ax2.plot(df_rent['DATE'], df_rent['pindex_renting'], 
             label='Renting Index (Right Axis)', color='forestgreen', linewidth=2, linestyle='--', marker='v', markersize=4)
    
    ax2.set_ylabel('Rent Index (Value)', color='forestgreen', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='forestgreen')
    
    # Consolidate Legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='white')
else:
    ax1.legend(loc='upper left')

plt.xlim(pd.Timestamp('2008-01-01'), pd.Timestamp('2025-1-1'))
plt.title('RWI Price Indices (Annual Observations)', fontsize=14)
plt.ylabel('Index Value')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()