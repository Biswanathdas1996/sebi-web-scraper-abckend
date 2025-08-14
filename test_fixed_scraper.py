"""Test the fixed scraper with just one page to see if it can extract the PDF correctly."""
from table_scraper_fixed import find_pdfs_on_page, download_pdf
import requests
from pathlib import Path

def test_fixed_scraper():
    url = "https://www.sebi.gov.in/legal/circulars/aug-2025/use-of-liquid-mutual-funds-and-overnight-mutual-funds-for-compliance-with-deposit-requirement-by-investment-advisers-and-research-analysts_96052.html"
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"})
    
    print(f"🧪 Testing fixed PDF extraction from: {url}")
    
    pdf_urls = find_pdfs_on_page(session, url)
    
    if pdf_urls:
        print(f"\n✅ Found {len(pdf_urls)} PDF(s):")
        for i, pdf_url in enumerate(pdf_urls, 1):
            print(f"   {i}. {pdf_url}")
        
        # Try to download the first PDF
        if pdf_urls:
            download_folder = Path("test_fixed_download")
            download_folder.mkdir(exist_ok=True)
            
            test_filename = download_folder / "test_fixed_sebi_circular.pdf"
            result = download_pdf(session, pdf_urls[0], test_filename)
            
            if result:
                print(f"\n📥 Downloaded test PDF to: {result}")
                print(f"📊 File size: {Path(result).stat().st_size} bytes")
            else:
                print(f"\n❌ Failed to download PDF")
    else:
        print("\n❌ No PDFs found")

if __name__ == "__main__":
    test_fixed_scraper()
