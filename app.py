from tool.webScrapper.ajax_scraper import scrape_page
from tool.fileReader.index import process_test_enhanced_metadata_pdfs
import json
import os

def test_enhanced_metadata():
    print("🧪 Testing enhanced metadata with date and circular number extraction...")
    
    # result = scrape_page(2, "test_enhanced_metadata")
    result = process_test_enhanced_metadata_pdfs()
    
    return result

if __name__ == "__main__":
    test_enhanced_metadata()
