import pdfplumber
import pandas as pd
import re

def clean_currency(val):
    if not val: return None
    # Remove euro signs, spaces, and convert German comma to dot
    cleaned = val.replace('€', '').replace(' ', '').strip()
    cleaned = re.sub(r',(\d{2})$', r'.\1', cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None

def parse_years(text):
    loc_flag = 'ALL'
    if 'Ost' in text: loc_flag = 'Ost'
    elif 'West' in text: loc_flag = 'West'
        
    if 'bis 1918' in text:
        return 0, 1918, loc_flag
        
    years = re.findall(r'(\d{4})', text)
    if len(years) >= 2:
        # Sort them to ensure min/max are correct, just in case
        years = sorted([int(y) for y in years[:2]])
        return years[0], years[1], loc_flag
        
    return None, None, None

def parse_sizes(text):
    text = text.lower()
    sizes = [float(s) for s in re.findall(r'(\d+)\s*m', text)]
    
    if 'alle wohnflächen' in text:
        return 0.0, 9999.0
        
    if 'bis unter' in text:
        if len(sizes) >= 2:
            return sizes[0], sizes[1] - 0.01
        elif len(sizes) == 1:
            return 0.0, sizes[0] - 0.01
    elif 'ab' in text and sizes:
        return sizes[-1], 9999.0
        
    return 0.0, 9999.0

def get_wohnlage(row_id):
    """Maps the row ID to the corresponding Wohnlage category."""
    if 1 <= row_id <= 49:
        return 'low'
    elif 50 <= row_id <= 117:
        return 'mid'
    elif 118 <= row_id <= 163:
        return 'good'
    return 'unknown'

def extract_with_regex(pdf_path, csv_path):
    parsed_rows = []
    
    current_b_min = 0
    current_b_max = 0
    current_loc = 'ALL'
    
    # 1. Extract raw text line-by-line
    raw_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True) 
            if text:
                raw_lines.extend(text.split('\n'))

    # 2. Process each line
    for line in raw_lines:
        line = line.strip()
        
        match = re.match(r'^([1-9]|[1-9]\d|1[0-5]\d|16[0-3])\s+(.*)', line)
        
        if match:
            row_id = int(match.group(1))
            content = match.group(2)
            
            prices = re.findall(r'(\d+,\d{2}\s*€?)', content)
            
            while len(prices) < 3:
                prices.append(None)
                
            r_min = clean_currency(prices[-3])
            r_avg = clean_currency(prices[-2])
            r_max = clean_currency(prices[-1])
            
            text_without_prices = re.sub(r'\d+,\d{2}\s*€?', '', content)
            
            # Forward Fill Years
            b_min, b_max, loc = parse_years(text_without_prices)
            if b_min is not None:
                current_b_min = b_min
                current_b_max = b_max
                current_loc = loc
                
            s_min, s_max = parse_sizes(text_without_prices)
            
            # Determine Wohnlage
            wohnlage = get_wohnlage(row_id)
            
            parsed_rows.append({
                'row_id': row_id,
                'wohnlage': wohnlage,
                'location_flag': current_loc,
                'buildingyear_min': current_b_min,
                'buildingyear_max': current_b_max,
                'size_lower': s_min,
                'size_upper': s_max,
                'rent_sqm_min': r_min,
                'rent_sqm_avg': r_avg,
                'rent_sqm_max': r_max
            })

    # 3. Validation and Export
    df = pd.DataFrame(parsed_rows)
    
    # Validation A: Check for exactly 163 rows
    found_ids = df['row_id'].tolist()
    missing_ids = [i for i in range(1, 164) if i not in found_ids]
    
    if len(df) != 163:
        print(f"⚠️ WARNING: Found {len(df)} rows.")
        if missing_ids:
            print(f"Missing row IDs: {missing_ids}")
    else:
        print("✅ SUCCESS: Found exactly 163 rows.")
        
    # Validation B: Uniqueness Check
    if df['row_id'].is_unique:
        print("✅ SUCCESS: All row IDs are unique.")
    else:
        duplicates = df[df.duplicated(['row_id'], keep=False)]
        print(f"⚠️ WARNING: Found duplicate row IDs: {duplicates['row_id'].unique().tolist()}")
        
    # Drop row_id to match your strict schema requirements and include wohnlage
    final_cols = ['wohnlage', 'buildingyear_min', 'buildingyear_max', 'size_lower', 'size_upper', 
                  'rent_sqm_min', 'rent_sqm_avg', 'rent_sqm_max', 'location_flag']
    
    df[final_cols].to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Data saved to {csv_path}")

# Run it
extract_with_regex('data/berlin/489.pdf', 'exports/ber_24_rent_grid.csv')