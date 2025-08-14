"""Run the complete scraper on SEBI website."""
from complete_scraper_with_pdfs import complete_scraper_with_pdfs

def run_complete_scraper():
    """Run the complete scraper with PDF downloads AND JSON metadata generation."""
    print("[START] Starting complete SEBI PDF scraper with downloads and JSON metadata")
    print("[INFO] This will download PDFs and generate metadata.json at the base directory level")
    print("\n" + "="*60)
    
    # Run complete scraper with PDF downloads
    complete_scraper_with_pdfs()

if __name__ == "__main__":
    run_complete_scraper()
