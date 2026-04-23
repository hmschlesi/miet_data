import requests
import sqlite3

# ==========================================
# CONFIGURATION
# ==========================================
DB_PATH = 'db/miet_data.db'
BERLIN_2024_UUID = "e7b9a5d1-3b4a-4c2d-9876-1a2b3c4d5e6f"

# The official Berlin WFS API URL
API_URL = (
    "https://gdi.berlin.de/services/wfs/adressen_rbs?"
    "service=WFS&version=2.0.0&request=GetFeature&"
    "typeNames=adressen_rbs:adressen_rbs&outputFormat=application/json&"
    "propertyName=strnam,hausnr,hausnrz,postleit,whn_lage,bez_name"
)

def update_berlin_addresses():
    # 1. Connect to the existing DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Ensure the table exists (in case this script runs first)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS berlin_addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id TEXT NOT NULL,
            zip TEXT,
            street TEXT,
            house_nr TEXT,
            house_nr_zusatz TEXT,
            district TEXT,
            wohnlage TEXT,
            FOREIGN KEY (catalog_id) REFERENCES mietspiegel_catalog (id)
        )
    ''')

    # 3. Fetch data from the API
    print("Fetching Berlin Address data (this can take a moment)...")
    try:
        response = requests.get(API_URL, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Error fetching API: {e}")
        return

    # 4. Parse features
    records_to_insert = []
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        records_to_insert.append((
            BERLIN_2024_UUID,
            props.get('postleit'),
            props.get('strnam'),
            props.get('hausnr'),
            props.get('hausnrz'),
            props.get('bez_name'),
            props.get('whn_lage')
        ))

    # 5. Transaction: Clear old data and insert new
    print(f"Saving {len(records_to_insert)} records to {DB_PATH}...")
    try:
        # We only delete addresses tied to the Berlin 2024 catalog
        cursor.execute('DELETE FROM berlin_addresses WHERE catalog_id = ?', (BERLIN_2024_UUID,))
        
        cursor.executemany('''
            INSERT INTO berlin_addresses (catalog_id, zip, street, house_nr, house_nr_zusatz, district, wohnlage) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', records_to_insert)
        
        conn.commit()
        print("✅ Berlin addresses updated successfully.")
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_berlin_addresses()