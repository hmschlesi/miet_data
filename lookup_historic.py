import sqlite3
import argparse
import sys
import os

DB_PATH = 'db/miet_data.db'

WOHNLAGE_MAPPING = {
    "1": "low",
    "2": "mid",
    "3": "good"
}

def get_zip_distribution(zip_code):
    """Analyzes the address database to find the % distribution of quality levels."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT wohnlage, COUNT(*) FROM berlin_addresses WHERE zip = ? GROUP BY wohnlage', (str(zip_code),))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows: return None

    total = sum(row[1] for row in rows)
    dist = {v: 0.0 for v in WOHNLAGE_MAPPING.values()}
    for val, count in rows:
        key = WOHNLAGE_MAPPING.get(str(val))
        if key: dist[key] = count / total
    return dist

def get_wohnlage_from_address(street, house_nr, zip_code):
    """Finds exact quality for a specific address."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clean_street = street.replace(" ", "").replace(".", "").replace("ß", "ss").lower()
    query = '''
        SELECT wohnlage, district FROM berlin_addresses 
        WHERE LOWER(REPLACE(REPLACE(REPLACE(street, ' ', ''), '.', ''), 'ß', 'ss')) LIKE ?
          AND house_nr = ? AND zip = ? LIMIT 1
    '''
    cursor.execute(query, (f"{clean_street}%", str(house_nr), str(zip_code)))
    result = cursor.fetchone()
    conn.close()
    if result: return WOHNLAGE_MAPPING.get(str(result[0]), "mid"), result[1]
    return None, None

def lookup_historical_rent(zip_code, size, building_year, street=None, house_nr=None):
    if not os.path.exists(DB_PATH):
        return {"error": "Database not found."}

    # 1. Prepare Weights for Weighted Average
    zip_weights = get_zip_distribution(zip_code)
    
    # 2. Identify Specific Quality if address is given
    address_quality = None
    district = "Unknown"
    address_found = False

    if street and house_nr:
        address_quality, district = get_wohnlage_from_address(street, house_nr, zip_code)
        if address_quality:
            address_found = True

    # 3. Fetch Catalogs & Grid Data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, version_year FROM mietspiegel_catalog 
        WHERE ? BETWEEN zip_code_min AND zip_code_max 
        ORDER BY version_year DESC
    ''', (zip_code,))
    catalogs = cursor.fetchall()

    history = []
    for cat_id, year in catalogs:
        cursor.execute('''
            SELECT wohnlage, rent_sqm_min, rent_sqm_avg, rent_sqm_max
            FROM mietspiegel
            WHERE catalog_id = ? AND ? BETWEEN buildingyear_min AND buildingyear_max
              AND ? >= size_lower AND ? <= size_upper
        ''', (cat_id, building_year, size, size))
        
        rows = cursor.fetchall()
        grid_data = {row[0]: {"min": row[1], "avg": row[2], "max": row[3]} for row in rows}

        # --- A. Calculate Weighted Average ---
        w_min = w_avg = w_max = 0.0
        if zip_weights:
            for q_level, weight in zip_weights.items():
                if q_level in grid_data:
                    w_min += grid_data[q_level]["min"] * weight
                    w_avg += grid_data[q_level]["avg"] * weight
                    w_max += grid_data[q_level]["max"] * weight
        else:
            # Absolute fallback to Mid if no zip distribution exists
            if "mid" in grid_data:
                w_min, w_avg, w_max = grid_data["mid"]["min"], grid_data["mid"]["avg"], grid_data["mid"]["max"]

        # --- B. Get Address-Specific Values ---
        specific_vals = None
        if address_found and address_quality in grid_data:
            specific_vals = grid_data[address_quality]

        history.append({
            "year": year,
            "weighted": {"min": w_min, "avg": w_avg, "max": w_max},
            "specific": specific_vals,
            "details": grid_data
        })

    conn.close()

    # Contextual info for the title
    if address_found:
        context = f"Exact Address: {street} {house_nr} ({district}) - Quality: {address_quality.upper()}"
    else:
        parts = [f"{int(v*100)}% {k.upper()}" for k, v in zip_weights.items() if v > 0] if zip_weights else ["100% MID"]
        context = f"Weighted ZIP {zip_code} Average ({', '.join(parts)})"

    return {
        "history": history, 
        "context": context, 
        "address_found": address_found,
        "district": district
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=int, required=True)
    parser.add_argument("--size", type=float, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--street", type=str)
    parser.add_argument("--nr", type=str)
    args = parser.parse_args()

    data = lookup_historical_rent(args.zip, args.size, args.year, args.street, args.nr)
    if "error" in data:
        print(f"❌ {data['error']}"); return

    print(f"\n📍 {data['context']}")
    print(f"📏 {args.size} sqm | 🏗️ Built {args.year}\n")

    for entry in data['history']:
        print(f"📅 Mietspiegel {entry['year']}")
        
        # 1. Print Specific Result if available
        if entry['specific']:
            s = entry['specific']
            print(f"   [ADDRESS]   Min: {s['min']:>5.2f} | Avg: {s['avg']:>5.2f} | Max: {s['max']:>5.2f}")
        
        # 2. Print Weighted Result
        w = entry['weighted']
        print(f"   [ZIP AVG]   Min: {w['min']:>5.2f} | Avg: {w['avg']:>5.2f} | Max: {w['max']:>5.2f}")
        print("-" * 55)

if __name__ == "__main__":
    main()