import pdfplumber
import csv
from typing import List, Optional

class PDFParser:
    """
    A utility class to extract text and tables from PDF documents using pdfplumber.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_raw_text(self) -> str:
        """
        Extracts all raw text from the PDF, page by page.
        Best for paragraphs and unstructured data.
        """
        extracted_text = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        extracted_text.append(f"--- PAGE {page_num + 1} ---\n{text}")
            
            return "\n\n".join(extracted_text)
        
        except Exception as e:
            print(f"Error reading PDF text: {e}")
            return ""

    def extract_tables(self) -> List[List[List[Optional[str]]]]:
        """
        Extracts tables from the PDF.
        Returns a list of tables. Each table is a list of rows, and each row is a list of string cells.
        Best for Mietspiegel grids and structured matrices.
        """
        all_tables = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    # extract_tables() automatically detects grid lines and spacing
                    tables_on_page = page.extract_tables(table_settings={
                        "vertical_strategy": "lines", 
                        "horizontal_strategy": "lines",
                        "intersection_y_tolerance": 5,
                    })
                    
                    for table in tables_on_page:
                        # Clean up the extracted text (remove newlines inside cells)
                        cleaned_table = [
                            [cell.replace('\n', ' ').strip() if cell else '' for cell in row]
                            for row in table
                        ]
                        all_tables.append(cleaned_table)
                        
            return all_tables
            
        except Exception as e:
            print(f"Error reading PDF tables: {e}")
            return []

    def export_table_to_csv(self, table: List[List[str]], output_path: str):
        """
        Utility method to quickly dump an extracted table into a CSV for manual inspection.
        """
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table)
        print(f"Table successfully exported to {output_path}")


# ==========================================
# EXECUTION EXAMPLE
# ==========================================
if __name__ == "__main__":
    # Ensure you have your '68.pdf' file in the same directory, or provide the full path
    pdf_path = "data/berlin/68.pdf" 
    
    parser = PDFParser(pdf_path)

    # 1. Test Table Extraction (Recommended for Mietspiegel)
    print("Extracting tables...")
    tables = parser.extract_tables()
    
    if tables:
        print(f"Found {len(tables)} table(s) in the document.")
        
        # Let's look at the first 5 rows of the first table
        first_table = tables[0]
        for idx, row in enumerate(first_table[:5]):
            print(f"Row {idx}: {row}")
            
        # Optional: Dump to a raw CSV to see how pdfplumber interpreted the columns
        parser.export_table_to_csv(first_table, "raw_extracted_table.csv")
    else:
        print("No tables detected using structural extraction. You may need to rely on raw text.")

    # 2. Test Raw Text Extraction (Fallback)
    print("\nExtracting raw text...")
    raw_text = parser.extract_raw_text()
    
    # Print the first 500 characters
    print(raw_text[:500])