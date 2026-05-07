import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

# 1. Load the YEARLY CSV Data
file_path = 'data/RWI-GEO-REDX_PUF_v16/RWIGEOREDX_GRIDS_V16_PUF_YEAR_ABS.csv'
print("Loading Yearly RWI CSV...")
df = pd.read_csv(file_path, low_memory=False)

# Keep only valid numeric grids
df = df[df['grid'].str.match(r'^\d+_\d+$', na=False)].copy()

# 2. Extract coordinates and convert to meters for mapping
df[['easting_km', 'northing_km']] = df['grid'].str.split('_', expand=True).astype(float)
df['easting_m'] = df['easting_km'] * 1000
df['northing_m'] = df['northing_km'] * 1000

# 3. Choose the target year column
target_year = '2023'
target_col = f'pindex{target_year}'

# Load the German Bundesländer borders
print("Loading map boundaries...")
url_geojson = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/3_mittel.geo.json"
germany = gpd.read_file(url_geojson).to_crs(epsg=3035)

# 4. Set up the Side-by-Side Plot
fig, axes = plt.subplots(1, 2, figsize=(20, 10))
housing_types = ['HK', 'WK']
titles = ['House Purchases (HK)', 'Apartment Purchases (WK)']

# Find the global min and max prices to make the color scales consistent across both maps
# We'll use 5th and 95th percentiles to avoid extreme outliers washing out the colors
combined_data = df[df['housing_type'].isin(housing_types)].dropna(subset=[target_col])
vmin = combined_data[target_col].quantile(0.05)
vmax = combined_data[target_col].quantile(0.95)

# 5. Plot each map
for i, h_type in enumerate(housing_types):
    ax = axes[i]
    
    # Draw the borders
    germany.plot(ax=ax, facecolor='whitesmoke', edgecolor='black', linewidth=0.8)
    
    # Filter for the specific housing type and drop NA values for this year
    df_map = df[df['housing_type'] == h_type].dropna(subset=[target_col])
    
    # Plot the scatter points
    scatter = ax.scatter(
        x=df_map['easting_m'], 
        y=df_map['northing_m'], 
        c=df_map[target_col], 
        cmap='plasma',            
        s=8, 
        alpha=0.8,
        edgecolors='none',
        vmin=vmin, # Lock the color scale
        vmax=vmax  # Lock the color scale
    )
    
    # Formatting
    ax.set_title(f'{titles[i]} - Absolute Price Index ({target_year})', fontsize=14)
    ax.set_axis_off()

# Add a single colorbar for the whole figure
cbar = fig.colorbar(scatter, ax=axes.ravel().tolist(), shrink=0.7, pad=0.02)
cbar.set_label('Absolute Price Index (€/sqm)', rotation=270, labelpad=20)

plt.suptitle('RWI-GEO-REDX: Real Estate Price Comparison', fontsize=18, y=0.95)
plt.show()