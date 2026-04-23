import sqlite3
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Configuration
DB_PATH = 'db/miet_data.db'
GEOJSON_PATH = 'data/berlin/plz.geojson'

def generate_quality_map():
    # 1. Load the data from the database
    print("Reading quality data from database...")
    conn = sqlite3.connect(DB_PATH)
    
    # We cast wohnlage to float to calculate a meaningful average
    query = "SELECT zip, CAST(wohnlage AS FLOAT) as quality FROM berlin_addresses"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("❌ No data found in 'berlin_addresses' table.")
        return

    # 2. Calculate the "Wohnlage Index" per ZIP code
    # This gives us a value between 1.0 (all Low) and 3.0 (all Good)
    zip_stats = df.groupby('zip')['quality'].mean().reset_index()
    zip_stats['zip'] = zip_stats['zip'].astype(str) # Ensure string for joining

    # 3. Load the GeoJSON boundaries
    print(f"Loading boundaries from {GEOJSON_PATH}...")
    try:
        berlin_map = gpd.read_file(GEOJSON_PATH)
    except Exception as e:
        print(f"❌ Error loading GeoJSON: {e}")
        return

    # 4. Join the datasets
    # Note: GeoJSON columns are usually 'plz' or 'postal_code'. 
    # Adjust 'left_on' if your file uses a different column name.
    merged = berlin_map.merge(zip_stats, left_on='plz', right_on='zip', how='left')

    # 5. Visualization
    print("Rendering map...")
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))

    # Plotting the data
    # RdYlGn: Red (Low Quality) -> Yellow (Mid) -> Green (Good)
    plot = merged.plot(
        column='quality',
        cmap='RdYlGn',
        legend=True,
        ax=ax,
        edgecolor='white',
        linewidth=0.3,
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "black",
            "label": "No Data",
        },
        legend_kwds={
            'label': "Residential Quality Index (1.0=Low, 3.0=Good)",
            'orientation': "horizontal",
            'shrink': 0.5,
            'pad': 0.05
        }
    )

    # Adding aesthetic touches
    ax.set_title("Berlin Residential Quality (Wohnlage) by ZIP Code", fontsize=18, pad=20)
    ax.axis('off')

    # Save and show
    output_img = 'berlin_quality_distribution.png'
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"✅ Map successfully saved to {output_img}")
    plt.show()

if __name__ == "__main__":
    generate_quality_map()