import requests
import sqlite3

# The optimized WFS URL
api_url = "https://gdi.berlin.de/services/wfs/adressen_rbs?service=WFS&version=2.0.0&request=GetFeature&typeNames=adressen_rbs:adressen_rbs&outputFormat=application/json&propertyName=strnam,hausnr,hausnrz,postleit,whn_lage,bez_name"

print("Fetching data from Berlin API (this might take a minute)...")
response = requests.get(api_url)
data = response.json()

# Connect to local SQLite database
conn = sqlite3.connect('mietspiegel.db')
cursor = conn.cursor()

# Create a clean, small table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS adressen (
        zip TEXT,
        street TEXT,
        house_nr TEXT,
        house_nr_zusatz TEXT,
        district TEXT,
        wohnlage TEXT
    )
''')

print("Parsing and saving to local database...")
# Extract the properties from the GeoJSON features
records_to_insert = []
for feature in data.get('features', []):
    props = feature.get('properties', {})
    records_to_insert.append((
        props.get('postleit'),
        props.get('strnam'),
        props.get('hausnr'),
        props.get('hausnrz'),
        props.get('bez_name'),
        props.get('whn_lage')
    ))

# Insert everything at once for speed
cursor.executemany('''
    INSERT INTO adressen (zip, street, house_nr, house_nr_zusatz, district, wohnlage) 
    VALUES (?, ?, ?, ?, ?, ?)
''', records_to_insert)

conn.commit()
conn.close()

print(f"Success! Inserted {len(records_to_insert)} addresses.")