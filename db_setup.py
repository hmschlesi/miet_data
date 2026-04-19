import sqlite3
import pandas as pd
from datetime import datetime
import os

from models import MietspiegelCatalog, MietspiegelGrid



# ==========================================
# 2. DATABASE SETUP SCRIPT
# ==========================================

def setup_database():
    os.makedirs('db', exist_ok=True)
    db_path = 'db/miet_data.db'
    
    # Static UUIDs for reproducibility
    BERLIN_2024_UUID = "e7b9a5d1-3b4a-4c2d-9876-1a2b3c4d5e6f"
    KOELN_2025_UUID = "c8d9ef73-bf10-46bf-a094-0e440be2a301"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Catalog Table (Updated with ZIP codes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mietspiegel_catalog (
            id TEXT PRIMARY KEY,
            slug TEXT NOT NULL,
            display_name TEXT NOT NULL,
            version_year TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            calculation_logic TEXT NOT NULL,
            zip_code_min INTEGER NOT NULL,
            zip_code_max INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Create Grid Table (Updated with equipment_level)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mietspiegel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id TEXT NOT NULL,
            wohnlage TEXT,
            equipment_level INTEGER,
            buildingyear_min INTEGER,
            buildingyear_max INTEGER,
            size_lower REAL,
            size_upper REAL,
            rent_sqm_min REAL,
            rent_sqm_avg REAL,
            rent_sqm_max REAL,
            location_flag TEXT,
            FOREIGN KEY (catalog_id) REFERENCES mietspiegel_catalog (id)
        )
    ''')

    # ---------------------------------------------------------
    # A. Validate and Seed Catalog Data
    # ---------------------------------------------------------
    try:
        # We create Pydantic instances. If we made a typo here, Pydantic would crash the script immediately.
        berlin_catalog = MietspiegelCatalog(
            id=BERLIN_2024_UUID, slug="berlin", display_name="Berlin", version_year="2024",
            calculation_logic="street_lookup", zip_code_min=10115, zip_code_max=14199
        )
        koeln_catalog = MietspiegelCatalog(
            id=KOELN_2025_UUID, slug="koeln", display_name="Köln", version_year="2025",
            calculation_logic="group_span", zip_code_min=50667, zip_code_max=51149
        )
        
        # Prepare the tuple for SQLite, ensuring UUIDs and Dates are strings
        catalogs = [
            (str(c.id), c.slug, c.display_name, c.version_year, c.is_active, 
             c.calculation_logic, c.zip_code_min, c.zip_code_max, str(c.created_at))
            for c in [berlin_catalog, koeln_catalog]
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO mietspiegel_catalog 
            (id, slug, display_name, version_year, is_active, calculation_logic, zip_code_min, zip_code_max, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', catalogs)
        print("✅ Catalogs validated and seeded successfully.")
        
    except ValidationError as e:
        print(f"❌ Catalog Validation Error:\n{e}")
        return

    # ---------------------------------------------------------
    # B. Validate and Load Berlin CSV
    # ---------------------------------------------------------
    csv_path = 'exports/ber_24_rent_grid.csv'
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        # Inject constants needed for the model
        df['catalog_id'] = BERLIN_2024_UUID
        df['equipment_level'] = None
        
        validated_rows = []
        
        # Pass every row through the Pydantic model
        try:
            for _, row in df.iterrows():
                # Convert the pandas row to a dict and unpack it into the Pydantic model
                grid_row = MietspiegelGrid(**row.to_dict())
                
                # If it passes, dump it back to a dict (converting UUIDs to strings for SQLite)
                dumped_row = grid_row.model_dump(mode='json')
                validated_rows.append(dumped_row)
                
            # Reconstruct a clean DataFrame from the validated data
            validated_df = pd.DataFrame(validated_rows)
            
            # Ensure column order matches the database exactly
            columns_to_insert = [
                'catalog_id', 'wohnlage', 'equipment_level', 'buildingyear_min', 'buildingyear_max', 
                'size_lower', 'size_upper', 'rent_sqm_min', 'rent_sqm_avg', 
                'rent_sqm_max', 'location_flag'
            ]
            validated_df = validated_df[columns_to_insert]
            
            # Insert into DB
            cursor.execute('DELETE FROM mietspiegel WHERE catalog_id = ?', (BERLIN_2024_UUID,))
            validated_df.to_sql('mietspiegel', conn, if_exists='append', index=False)
            
            print(f"✅ Inserted {len(validated_df)} strictly validated rows for Berlin 2024.")
            
        except ValidationError as e:
            print(f"❌ Grid Validation Error in CSV Data:\n{e}")
            # The script will safely exit without corrupting the database
    else:
        print(f"⚠️ Could not find {csv_path}. Skipping Berlin grid insertion.")

    # Commit and close
    conn.commit()
    conn.close()
    print(f"✅ Database setup complete! Saved to: {db_path}")

if __name__ == "__main__":
    setup_database()