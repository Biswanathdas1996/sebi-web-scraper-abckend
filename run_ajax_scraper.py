#!/usr/bin/env python3
"""
Test script to verify enhanced metadata with date and circular number extraction
"""

from ajax_scraper import scrape_page
import json
import os

def test_enhanced_metadata():
    print("🧪 Testing enhanced metadata with date and circular number extraction...")
    
    # Test with single page
    result = scrape_page(2, "test_enhanced_metadata")
    
    print(f"\n✅ Test completed!")
    print(f"   📄 Page processed: 1")
    print(f"   🔗 Links found: {result['links_found']}")
    print(f"   📥 Files downloaded: {result['downloaded_files']}")
    
    # Check metadata file
    metadata_file = os.path.join(result['download_path'], 'scraping_metadata.json')
    if os.path.exists(metadata_file):
        print(f"   💾 ✅ Enhanced metadata JSON created!")
        
        # Load and display sample data
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"\n📊 Sample link with extracted info:")
        if metadata.get('links') and len(metadata['links']) > 0:
            sample_link = metadata['links'][0]
            print(f"   📋 Title: {sample_link['text'][:60]}...")
            print(f"   📅 Date (URL): {sample_link.get('circular_date', 'N/A')}")
            print(f"   📅 Month-Year: {sample_link.get('circular_month_year_full', 'N/A')}")
            print(f"   🔢 Circular Number (URL): {sample_link.get('circular_number', 'N/A')}")
            print(f"   🖼️  Has iframe: {sample_link.get('has_iframe', 'N/A')}")
            print(f"   🌐 URL: {sample_link['url']}")
        
        print(f"\n📊 Sample file with extracted info:")
        if metadata.get('files') and len(metadata['files']) > 0:
            sample_file = metadata['files'][0]
            if isinstance(sample_file, dict):
                print(f"   📁 Filename: {sample_file.get('original_filename', 'N/A')}")
                print(f"   📅 Date (page): {sample_file.get('circular_date', 'N/A')}")
                print(f"   📅 Month-Year: {sample_file.get('circular_month_year_full', 'N/A')}")
                
                # Show circular number priority
                sebi_ref = sample_file.get('sebi_circular_ref', '')
                url_circular = sample_file.get('circular_number', '')
                page_circular = sample_file.get('page_circular_number', '')
                
                print(f"   � SEBI Circular Reference: {sebi_ref if sebi_ref else 'N/A'}")
                print(f"   🔢 URL Circular ID: {url_circular}")
                print(f"   🔢 Page Circular Number: {page_circular if page_circular else 'N/A'}")
                
                # Show which one is being used as primary
                primary_circular = sebi_ref or page_circular or url_circular or "N/A"
                print(f"   ✅ Primary Circular Number: {primary_circular}")
                
                print(f"   🖼️  Has iframe: {sample_file.get('has_iframe', 'N/A')}")
                print(f"   📏 File Size: {sample_file.get('file_size', 0)} bytes")
                print(f"   📖 Source Text: {sample_file.get('link_text', 'N/A')[:50]}...")
    else:
        print(f"   ❌ Metadata file not found!")
    
    return result

if __name__ == "__main__":
    test_enhanced_metadata()
