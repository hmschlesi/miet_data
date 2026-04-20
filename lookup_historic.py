import sqlite3
import argparse
import sys
import os

DB_PATH = 'db/miet_data.db'

def lookup_historical_rent(zip_code, size, building_year, wohnlage=None):
    """
    Looks up the base rent from ALL matching Mietspiegel catalogs in the database.
    Returns a dictionary grouped by the catalog's version year.
    """
    if not os.path.exists(DB_PATH):
        return {"error": f"Database not found at {DB_PATH}. Please run the setup script first."}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Identify ALL Catalogs via ZIP Code (Ignoring is_active)
    cursor.execute('''
        SELECT id, display_name, version_year, calculation_logic 
        FROM mietspiegel_catalog 
        WHERE ? BETWEEN zip_code_min AND zip_code_max
        ORDER BY version_year DESC
    ''', (zip_code,))
    
    catalogs = cursor.fetchall()
    
    if not catalogs:
        conn.close()
        return {"error": f"No Mietspiegel catalogs found for ZIP code {zip_code}."}

    # Assume the ZIP code maps to the same city across years
    city_name = catalogs[0][1] 
    historical_data = []

    # 2. Iterate through each matching catalog and query its specific grid
    for catalog in catalogs:
        catalog_id, _, version_year, calc_logic = catalog
        
        query = '''
            SELECT wohnlage, rent_sqm_min, rent_sqm_avg, rent_sqm_max, location_flag
            FROM mietspiegel
            WHERE catalog_id = ?
              AND ? BETWEEN buildingyear_min AND buildingyear_max
              AND ? >= size_lower AND ? <= size_upper
        '''
        params = [catalog_id, building_year, size, size]
        
        # Dynamically append the Wohnlage filter if provided
        if wohnlage:
            query += " AND wohnlage = ?"
            params.append(wohnlage.lower())

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Format the results for this specific year
        spans = []
        for row in results:
            spans.append({
                "wohnlage": row[0],
                "rent_min": row[1],
                "rent_avg": row[2],
                "rent_max": row[3],
                "location_flag": row[4]
            })

        historical_data.append({
            "version_year": version_year,
            "calculation_logic": calc_logic,
            "results": spans
        })

    conn.close()

    return {
        "status": "Success",
        "city": city_name,
        "history": historical_data
    }

def main():
    parser = argparse.ArgumentParser(description="Historical Mietspiegel Base Rent Lookup CLI")
    parser.add_argument("--zip", type=int, required=True, help="5-digit ZIP code (e.g., 10115)")
    parser.add_argument("--size", type=float, required=True, help="Apartment size in sqm (e.g., 65.5)")
    parser.add_argument("--year", type=int, required=True, help="Year of construction (e.g., 1980)")
    parser.add_argument("--wohnlage", type=str, choices=['low', 'mid', 'good'], help="Optional: Specific area quality (low, mid, good)")
    
    args = parser.parse_args()

    wohnlage_str = f" | Wohnlage: {args.wohnlage.upper()}" if args.wohnlage else ""
    print(f"\n🔍 Looking up historical base rent for: {args.size} sqm | Built {args.year} | ZIP: {args.zip}{wohnlage_str}")
    print("-" * 75)
    
    response = lookup_historical_rent(args.zip, args.size, args.year, args.wohnlage)

    if "error" in response:
        print(f"❌ Error: {response['error']}")
        sys.exit(1)

    print(f"📍 City: {response['city']}\n")
    
    # Loop through the history and print the progression
    for entry in response['history']:
        print(f"📅 Mietspiegel {entry['version_year']} (Logic: {entry['calculation_logic']})")
        
        if not entry['results']:
            print("   ⚠️ No matching grid data found in this catalog for these parameters.\n")
            continue
            
        for span in entry['results']:
            loc_str = f" (Location: {span['location_flag']})" if span['location_flag'] != 'ALL' else ""
            print(f"   ▶ Wohnlage: {span['wohnlage'].upper()}{loc_str}")
            print(f"      Min: {span['rent_min']:.2f} €/sqm")
            print(f"      Avg: {span['rent_avg']:.2f} €/sqm")
            print(f"      Max: {span['rent_max']:.2f} €/sqm\n")

if __name__ == "__main__":
    main()