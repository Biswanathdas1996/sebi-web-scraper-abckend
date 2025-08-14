"""Run the complete scraper on SEBI website."""
from table_scraper_fixed import scrape_sample_table

def run_complete_scraper():
    """Run the complete scraper on SEBI website."""
    url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
    folder = "sebi_circulars_pdfs"
    
    print("🚀 Starting complete SEBI PDF scraper")
    print(f"📍 Target: Table with id='sample_1'")
    print(f"🎯 Looking for iframe PDFs in each table link")
    print(f"📁 Download folder: {folder}")
    print("\n" + "="*60)
    
    scrape_sample_table(url, folder)

if __name__ == "__main__":
    run_complete_scraper()
