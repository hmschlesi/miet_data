import sqlite3

# Connect to your newly created database
conn = sqlite3.connect('mietspiegel.db')
cursor = conn.cursor()

# We use LIKE for the street name to catch "Böhmische Str." or "Böhmische Straße"
# Note: SQLite LIKE is case-insensitive by default, which is great for user input!
query = """
    SELECT district, street, house_nr, house_nr_zusatz, wohnlage 
    FROM adressen 
    WHERE street LIKE ?  
      AND house_nr = ?
"""

# The parameters from your LLM parser
search_zip = '12055'
search_street = 'Böhmische Str%' # The % is a wildcard
search_house_nr = '30'

cursor.execute(query, (search_street, search_house_nr))
results = cursor.fetchall()

if results:
    for row in results:
        district, street, house_nr, zusatz, wohnlage = row
        
        # Clean up the 'zusatz' (house letter) if it's None
        full_house_nr = f"{house_nr}{zusatz if zusatz else ''}"
        
        print("--- Match Found ---")
        print(f"Address:  {street} {full_house_nr}, Berlin ({district})")
        print(f"Wohnlage: {wohnlage}")
else:
    print("No exact match found. (Fallback to street average logic!)")

conn.close()