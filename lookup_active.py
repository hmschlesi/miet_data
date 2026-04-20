import sqlite3
import argparse
import sys
import os

DB_PATH = 'db/miet_data.db'

def calculate_base_rent(zip_code, size, building_year, wohnlage=None):
    """
    Looks up the base rent from the database based on ZIP code, size, year, and optionally Wohnlage.
    Returns a dictionary with the catalog info and matching rent spans.
    """
    if not os.path.exists(DB_PATH):
        return {"error": f"Database not found at {DB_PATH}. Please run the setup script first."}

    # 1. Hardcoded Bypass: New Build Exemption
    if building_year >= 2014:
        return {
            "status": "Exempt",
            "message": f"Construction year {building_year} qualifies as a New Build and is exempt from standard base rent caps."
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Identify the active Catalog via ZIP Code
    cursor.execute('''
        SELECT id, display_name, calculation_logic 
        FROM mietspiegel_catalog 
        WHERE is_active = 1 
          AND ? BETWEEN zip_code_min AND zip_code_max
    ''', (zip_code,))
    
    catalog_match = cursor.fetchone()
    
    if not catalog_match:
        conn.close()
        return {"error": f"No active Mietspiegel found for ZIP code {zip_code}."}

    catalog_id, city_name, calc_logic = catalog_match

    # 3. Build and execute the dynamic Query for the Mietspiegel Grid
    query = '''
        SELECT wohnlage, rent_sqm_min, rent_sqm_avg, rent_sqm_max, location_flag
        FROM mietspiegel
        WHERE catalog_id = ?
          AND ? BETWEEN buildingyear_min AND buildingyear_max
          AND ? >= size_lower AND ? <= size_upper
    '''
    params = [catalog_id, building_year, size, size]
    
    # Dynamically append the Wohnlage filter if the user provided it
    if wohnlage:
        query += " AND wohnlage = ?"
        params.append(wohnlage.lower())

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        err_msg = "No matching grid data found for this specific size and year combination."
        if wohnlage:
            err_msg = f"No matching grid data found for {size} sqm, built {building_year}, in '{wohnlage}' wohnlage."
        return {
            "city": city_name,
            "error": err_msg
        }

    # Format the results
    spans = []
    for row in results:
        spans.append({
            "wohnlage": row[0],
            "rent_min": row[1],
            "rent_avg": row[2],
            "rent_max": row[3],
            "location_flag": row[4]
        })

    return {
        "status": "Success",
        "city": city_name,
        "calculation_logic": calc_logic,
        "results": spans
    }

def main():
    parser = argparse.ArgumentParser(description="Mietspiegel Base Rent Lookup CLI")
    parser.add_argument("--zip", type=int, required=True, help="5-digit ZIP code (e.g., 10437)")
    parser.add_argument("--size", type=float, required=True, help="Apartment size in sqm (e.g., 65.5)")
    parser.add_argument("--year", type=int, required=True, help="Year of construction (e.g., 1980)")
    parser.add_argument("--wohnlage", type=str, choices=['low', 'mid', 'good'], help="Optional: Specific area quality (low, mid, good)")
    
    args = parser.parse_args()

    wohnlage_str = f" | Wohnlage: {args.wohnlage.upper()}" if args.wohnlage else ""
    print(f"\n🔍 Looking up base rent for: {args.size} sqm | Built {args.year} | ZIP: {args.zip}{wohnlage_str}")
    print("-" * 60)
    
    response = calculate_base_rent(args.zip, args.size, args.year, args.wohnlage)

    if "error" in response:
        print(f"❌ Error: {response['error']}")
        sys.exit(1)
        
    if response.get("status") == "Exempt":
        print(f"⚠️  Status: {response['status']}")
        print(f"ℹ️  {response['message']}")
        sys.exit(0)

    print(f"📍 City: {response['city']} (Logic: {response['calculation_logic']})")
    print(f"📊 Matching Base Rent Spans:\n")
    
    for span in response['results']:
        loc_str = f" (Location: {span['location_flag']})" if span['location_flag'] != 'ALL' else ""
        print(f"   ▶ Wohnlage: {span['wohnlage'].upper()}{loc_str}")
        print(f"      Min: {span['rent_min']:.2f} €/sqm")
        print(f"      Avg: {span['rent_avg']:.2f} €/sqm")
        print(f"      Max: {span['rent_max']:.2f} €/sqm\n")

if __name__ == "__main__":
    main()