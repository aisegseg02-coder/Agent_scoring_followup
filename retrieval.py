import os
import json
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text

# Sector PDF Path
SECTOR_ENGINE_PATH = r"E:\Rag\Sector_Engine"

# Fetch PDFs from Sector
def fetch_pdfs_from_sector(sector):
    sector_path = os.path.join(SECTOR_ENGINE_PATH, sector)
    pdf_files = []
    if os.path.exists(sector_path) and os.path.isdir(sector_path):
        pdf_files = [
            os.path.join(sector_path, f)
            for f in os.listdir(sector_path)
            if f.lower().endswith(".pdf")
        ]
    return pdf_files

# Extract text using PyPDF2 (Fallback method)
def extract_text_from_pdf_pypdf2(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

# Extract text using PDFMiner (More robust for Arabic content)
def extract_text_from_pdf_pdfminer(pdf_path):
    try:
        raw_text = extract_text(pdf_path)
        print("Raw Text Extracted from PDF:", raw_text)  # Print raw extracted text for debugging
        return raw_text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

# Combine extraction methods to get best result
def extract_text_from_pdf(pdf_path):
    # Try both PyPDF2 and pdfminer
    text = extract_text_from_pdf_pypdf2(pdf_path)
    if not text.strip():  # if PyPDF2 didn't extract text, use pdfminer
        text = extract_text_from_pdf_pdfminer(pdf_path)
    return text

# Process all PDFs in a sector
def process_pdfs_for_sector(sector):
    pdf_files = fetch_pdfs_from_sector(sector)
    sector_data = {}
    
    for pdf_file in pdf_files:
        print(f"Extracting text from {pdf_file}...")
        raw_text = extract_text_from_pdf(pdf_file)  # Get raw text
        
        if raw_text:
            print("Raw Text before cleaning:", raw_text)  # Debug: Print raw text
        
        # Clean the extracted text (optional normalization)
        clean_text = raw_text.strip().replace("\n", " ").replace("  ", " ")
        
        # Debug: Print cleaned text
        print(f"Cleaned Text for {pdf_file}: {clean_text}")
        
        # Store the cleaned content in the sector data
        sector_data[os.path.basename(pdf_file)] = clean_text
    
    return sector_data

# Example usage
def cache_pdf_content():
    sector = "Marketing"  # Define the sector you want to process
    sector_data = process_pdfs_for_sector(sector)

    # Save the extracted data into a JSON file for fast retrieval
    with open(f"{sector}_cached_data.json", "w", encoding="utf-8") as file:
        json.dump(sector_data, file, ensure_ascii=False, indent=2)

    print(f"Cached content for sector: {sector}")
    return sector_data

# Load and retrieve cached data (for speed optimization)
def load_cached_data():
    sector = "Marketing"
    cached_file = f"{sector}_cached_data.json"

    if os.path.exists(cached_file):
        with open(cached_file, "r", encoding="utf-8") as file:
            sector_data = json.load(file)
        print(f"Loaded cached data for sector: {sector}")
        return sector_data
    else:
        print(f"No cached data found for sector: {sector}")
        return cache_pdf_content()

# Example to demonstrate the PDF processing and caching
if __name__ == "__main__":
    cached_data = load_cached_data()  # Try loading cached data, if not, process PDFs
    print("\n=== Cached PDF Content ===")
    for pdf_name, content in cached_data.items():
        print(f"\nPDF: {pdf_name}\nContent: {content}\n")
