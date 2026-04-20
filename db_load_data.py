import sqlite3
import pandas as pd
import os
import uuid
from pydantic import ValidationError

# Assuming your models are in models.py
from models import MietspiegelCatalog, MietspiegelGrid

def load_mietspiegel(db_path: str, csv_path: str, catalog_data: dict):
    """
    Validates and loads a single Mietspiegel catalog and its corresponding CSV grid into the DB.
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ Skipping {catalog_data['version_year']}: CSV not found at {csv_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Validate and Insert Catalog
        catalog = MietspiegelCatalog(**catalog_data)
        
        cursor.execute('''
            INSERT OR REPLACE INTO mietspiegel_catalog 
            (id, slug, display_name, version_year, is_active, calculation_logic, zip_code_min, zip_code_max, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(catalog.id), catalog.slug, catalog.display_name, catalog.version_year, 
              catalog.is_active, catalog.calculation_logic, catalog.zip_code_min, 
              catalog.zip_code_max, str(catalog.created_at)))

        # 2. Read and Validate Grid CSV
        df = pd.read_csv(csv_path)
        df['catalog_id'] = catalog.id
        if 'equipment_level' not in df.columns:
            df['equipment_level'] = None
        
        validated_rows = []
        for _, row in df.iterrows():
            # 1. Convert to dictionary first
            row_dict = row.to_dict()
            
            # 2. THE MISSING LINE: Loop through and destroy any NaN values, replacing them with None
            clean_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            
            # 3. Pass the CLEANED dictionary to Pydantic, NOT row.to_dict()
            grid_row = MietspiegelGrid(**clean_dict)
            
            validated_rows.append(grid_row.model_dump(mode='json'))

        validated_df = pd.DataFrame(validated_rows)
        
        # Ensure correct column order
        columns_to_insert = [
            'catalog_id', 'wohnlage', 'equipment_level', 'buildingyear_min', 'buildingyear_max', 
            'size_lower', 'size_upper', 'rent_sqm_min', 'rent_sqm_avg', 'rent_sqm_max', 'location_flag'
        ]
        validated_df = validated_df[columns_to_insert]
        
        # 3. Clear old data for this catalog (prevents duplicates on re-runs) and Insert
        cursor.execute('DELETE FROM mietspiegel WHERE catalog_id = ?', (str(catalog.id),))
        validated_df.to_sql('mietspiegel', conn, if_exists='append', index=False)
        
        conn.commit()
        print(f"✅ Successfully loaded {catalog.display_name} {catalog.version_year} ({len(validated_df)} rows).")
        
    except ValidationError as e:
        print(f"❌ Validation Error for {catalog_data['version_year']}:\n{e}")
        conn.rollback()
    except Exception as e:
        print(f"❌ Database Error for {catalog_data['version_year']}: {e}")
        conn.rollback()
    finally:
        conn.close()

# ==========================================
# EXECUTION
# ==========================================

if __name__ == "__main__":
    DATABASE_PATH = 'db/miet_data.db'
    
    # Define all the datasets you want to add here. 
    # Generating UUIDs deterministically (or explicitly) prevents duplicates.
    datasets_to_load = [
        {
            "csv_path": "exports/ber_19_rent_grid.csv",
            "catalog_data": {
                "id": uuid.uuid4(),
                "slug": "berlin",
                "display_name": "Berlin",
                "version_year": "2019",
                "is_active": False,
                "calculation_logic": "street_lookup",
                "zip_code_min": 10115,
                "zip_code_max": 14199
            }
        },
    ]

    for dataset in datasets_to_load:
        load_mietspiegel(
            db_path=DATABASE_PATH,
            csv_path=dataset["csv_path"],
            catalog_data=dataset["catalog_data"]
        )