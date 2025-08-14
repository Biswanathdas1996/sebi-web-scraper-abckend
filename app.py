#!/usr/bin/env python3
"""
Test script to verify enhanced metadata with date and circular number extraction
"""

from tool.webScrapper.ajax_scraper import scrape_page
import json
import os

def test_enhanced_metadata():
    print("🧪 Testing enhanced metadata with date and circular number extraction...")
    
    # Test with single page
    result = scrape_page(2, "test_enhanced_metadata")
    
    
    
    return result

if __name__ == "__main__":
    test_enhanced_metadata()
