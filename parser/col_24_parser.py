import pdfplumber
import pandas as pd
import re

def clean_and_split_prices(price_string):
    """
    Takes a messy string like '4,70-7,20', '7,50 9,60', or '7,509,60' 
    and returns a tuple of floats (min, max).
    """
    # Remove € signs and whitespace
    clean_str = price_string.replace('€', '').replace(' ', '')
    
    # Insert a dash if it's completely missing but we have 6 digits (e.g., 7,509,60 -> 7,50-9,60)
    if re.match(r'^\d,\d{2}\d,\d{2}$', clean_str):
        clean_str = clean_str[:4] + '-' + clean_str[4:]
        
    # Find all floats formatted like German currency (X,XX)
    prices = re.findall(r'(\d+,\d{2})', clean_str)
    
    if len(prices) >= 2:
        p_min = float(prices[0].replace(',', '.'))
        p_max = float(prices[1].replace(',', '.'))
        p_avg = round((p_min + p_max) / 2, 2) # Calculate our own average
        return p_min, p_avg, p_max
    return None, None, None

def parse_cologne_pdf(pdf_path, csv_path):
    parsed_rows = []
    
    current_b_min = 0
    current_b_max = 9999
    current_s_min = 0.0
    current_s_max = 9999.0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
                
            for line in text.split('\n'):
                line = line.strip()
                
                # 1. Catch the Building Years (GRUPPE)
                if 'bezugsfertig' in line.lower():
                    years = re.findall(r'(\d{4})', line)
                    if 'bis' in line and len(years) == 1:
                        current_b_min, current_b_max = 0, int(years[0])
                    elif 'ab' in line and len(years) == 1:
                        current_b_min, current_b_max = int(years[0]), 9999
                    elif len(years) == 2:
                        current_b_min, current_b_max = int(years[0]), int(years[1])
                        
                # 2. Catch the Apartment Sizes (A, B, C, D, E)
                size_match = re.search(r'([A-E])\s*Wohnungen.*?(\d+)\s*m²\s*-\s*(\d+,?\d*)\s*m²', line)
                if size_match:
                    current_s_min = float(size_match.group(2).replace(',', '.'))
                    current_s_max = float(size_match.group(3).replace(',', '.'))
                
                # Also check Group E which usually just has one size bound (e.g., 110 m2 - 140 m2)
                # Note: The PDF stops at 140m2, but we'll leave it open-ended for our calculator
                if '110' in line and '140' in line:
                    current_s_min, current_s_max = 110.0, 9999.0
                    
                # 3. Catch the Equipment Level & Prices (Starts with 1, 2, or 3)
                eq_match = re.match(r'^([123])\s+(.*)', line)
                
                # Group 6 doesn't have 1,2,3 equipment levels, it just has the sizes and prices directly on the line
                is_group_6 = current_b_min >= 2018
                
                if eq_match or is_group_6:
                    # If Group 6, we just parse the whole line. If 1-5, we parse everything after the equipment number.
                    content = eq_match.group(2) if eq_match else line
                    equipment_level = int(eq_match.group(1)) if eq_match else 3 # Defaulting modern builds to high equipment
                    
                    # Split the content by large gaps of whitespace to isolate the columns
                    columns = re.split(r'\s{3,}', content)
                    
                    # Ensure we have exactly 3 columns to process (Low, Mid, Good)
                    # This helps us handle missing data cells
                    prices = [c for c in columns if re.search(r'\d,\d{2}', c)]
                    
                    wohnlagen = ['low', 'mid', 'good']
                    
                    for idx, price_block in enumerate(prices):
                        if idx > 2: break
                        
                        p_min, p_avg, p_max = clean_and_split_prices(price_block)
                        
                        if p_min is not None:
                            parsed_rows.append({
                                'wohnlage': wohnlagen[idx],
                                'equipment_level': equipment_level,
                                'buildingyear_min': current_b_min,
                                'buildingyear_max': current_b_max,
                                'size_lower': current_s_min,
                                'size_upper': current_s_max,
                                'rent_sqm_min': p_min,
                                'rent_sqm_avg': p_avg,
                                'rent_sqm_max': p_max,
                                'location_flag': 'ALL' # Cologne doesn't have East/West splits
                            })

    df = pd.DataFrame(parsed_rows)
    
    # Export
    # We add 'equipment_level' to the schema just for Cologne
    final_cols = ['wohnlage', 'equipment_level', 'buildingyear_min', 'buildingyear_max', 
                  'size_lower', 'size_upper', 'rent_sqm_min', 'rent_sqm_avg', 'rent_sqm_max', 'location_flag']
    
    df[final_cols].to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ Data saved to {csv_path}. Found {len(df)} price spans.")

extract_cologne_pdf('data/koeln/Koeln_2025_1621.pdf', 'exports/koeln_mietspiegel_parsed.csv')