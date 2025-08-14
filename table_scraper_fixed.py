"""Simple scraper focused on table with id='sample_1' and td > a structure."""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}

def extract_circular_metadata(session: requests.Session, url: str) -> dict:
    """Extract date and circular number from a SEBI circular page, focusing on m_section bottom_space2 div."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Initialize metadata
        metadata = {
            "date": "Unknown",
            "circular_no": "Unknown"
        }
        
        # First, look specifically in the div with class="m_section bottom_space2"
        target_div = soup.find("div", class_="m_section bottom_space2")
        if target_div:
            print(f"   [TARGET] Found target div with class 'm_section bottom_space2'")
            div_text = target_div.get_text()
            div_html = str(target_div)
            
            # Enhanced date patterns - more comprehensive
            date_patterns = [
                r'Date\s*:?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s*,?\s*\d{4})',  # Date: 14th August, 2025
                r'Date\s*:?\s*([A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})',  # Date: August 14th, 2025
                r'Date\s*:?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',  # Date: 14/08/2025 or 14-08-2025
                r'Date\s*:?\s*(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})',  # Date: 2025/08/14
                r'Dated\s*:?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s*,?\s*\d{4})',  # Dated: 14th August, 2025
                r'Dated\s*:?\s*([A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})',  # Dated: August 14th, 2025
                r'Dated\s*:?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',  # Dated: 14/08/2025
                # Look for dates without "Date:" prefix
                r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s*,?\s*\d{4})',  # 14th August, 2025
                r'([A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})',  # August 14th, 2025
                r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',  # 14/08/2025 or 14-08-2025
            ]
            
            # Try to find date in div text
            for pattern in date_patterns:
                match = re.search(pattern, div_text, re.IGNORECASE)
                if match:
                    metadata["date"] = match.group(1).strip()
                    print(f"   [DATE] Found date in target div: {metadata['date']}")
                    break
            
            # Enhanced circular number patterns - more comprehensive
            circular_patterns = [
                # Complete SEBI circular formats with optional spaces
                r'(SEBI/HO/[A-Z0-9\-_/\s]+/P?/?CIR[A-Z0-9\-_/\s]*\d{4}/[A-Z0-9\-_/\s]+)',
                r'(SEBI/HO/[A-Z0-9\-_/\s]+/CIR/P/\d{4}/[A-Z0-9\-_/\s]+)',
                r'(SEBI/HO/[A-Z0-9\-_/\s]+/[A-Z0-9\-_/\s]*CIR[A-Z0-9\-_/\s]*\d+)',
                r'Circular\s+No\.?\s*:?\s*(SEBI/HO/[A-Z0-9\-_/\s]+)',
                r'Circular\s+Number\s*:?\s*(SEBI/HO/[A-Z0-9\-_/\s]+)',
                # Look for any SEBI reference number with spaces
                r'(SEBI/[A-Z0-9\-_/\s]+/\d{4}/[A-Z0-9\-_/\s]*)',
                r'Circular\s+No\.?\s*:?\s*([A-Z0-9/\-_.\s]{10,})',
                r'Circular\s+Number\s*:?\s*([A-Z0-9/\-_.\s]{10,})',
            ]
            
            # Try to find circular number in div text
            for pattern in circular_patterns:
                match = re.search(pattern, div_text, re.IGNORECASE)
                if match:
                    circular_found = match.group(1).strip()
                    # Clean up the circular number by removing extra spaces
                    circular_found = re.sub(r'\s+', ' ', circular_found)  # Replace multiple spaces with single space
                    circular_found = re.sub(r'(?<=/)\s+', '', circular_found)  # Remove spaces after slashes
                    circular_found = re.sub(r'\s+(?=/)', '', circular_found)  # Remove spaces before slashes
                    
                    # Only accept if it's reasonably long and looks like a circular number
                    if len(circular_found) > 8 and ('SEBI' in circular_found.upper() or 'CIR' in circular_found.upper()):
                        metadata["circular_no"] = circular_found
                        print(f"   [CIRCULAR] Found circular no in target div: {metadata['circular_no']}")
                        break
            
            # Also search in HTML content for better pattern matching
            for pattern in circular_patterns:
                match = re.search(pattern, div_html, re.IGNORECASE)
                if match and metadata["circular_no"] == "Unknown":
                    circular_found = match.group(1).strip()
                    # Clean up the circular number
                    circular_found = re.sub(r'\s+', ' ', circular_found)  # Replace multiple spaces with single space
                    circular_found = re.sub(r'(?<=/)\s+', '', circular_found)  # Remove spaces after slashes
                    circular_found = re.sub(r'\s+(?=/)', '', circular_found)  # Remove spaces before slashes
                    
                    if len(circular_found) > 8 and ('SEBI' in circular_found.upper() or 'CIR' in circular_found.upper()):
                        metadata["circular_no"] = circular_found
                        print(f"   [CIRCULAR] Found circular no in target div HTML: {metadata['circular_no']}")
                        break
        
        else:
            print(f"   [WARNING] Target div with class 'm_section bottom_space2' not found, using full page search")
            # Fallback to searching the entire page
            page_text = soup.get_text()
            
            # Search for date patterns in the full page
            date_patterns = [
                r'Date\s*:?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s*,?\s*\d{4})',
                r'Date\s*:?\s*([A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})',
                r'Date\s*:?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',
                r'Dated\s*:?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s*,?\s*\d{4})',
                r'Dated\s*:?\s*([A-Za-z]{3,9}\s+\d{1,2}(?:st|nd|rd|th)?\s*,?\s*\d{4})',
                r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',
                r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    metadata["date"] = match.group(1).strip()
                    print(f"   [DATE] Found date in full page: {metadata['date']}")
                    break
            
            # Search for circular number patterns in full page
            circular_patterns = [
                r'(SEBI/HO/[A-Z0-9\-_/\s]+/P?/?CIR[A-Z0-9\-_/\s]*\d{4}/[A-Z0-9\-_/\s]+)',
                r'Circular\s+No\.?\s*:?\s*(SEBI/HO/[A-Z0-9\-_/\s]+)',
                r'(SEBI/[A-Z0-9\-_/\s]+/\d{4}/[A-Z0-9\-_/\s]*)',
                r'Circular\s+No\.?\s*:?\s*([A-Z0-9/\-_.\s]{10,})',
            ]
            
            for pattern in circular_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    circular_found = match.group(1).strip()
                    # Clean up the circular number
                    circular_found = re.sub(r'\s+', ' ', circular_found)  # Replace multiple spaces with single space
                    circular_found = re.sub(r'(?<=/)\s+', '', circular_found)  # Remove spaces after slashes
                    circular_found = re.sub(r'\s+(?=/)', '', circular_found)  # Remove spaces before slashes
                    if len(circular_found) > 8:
                        metadata["circular_no"] = circular_found
                        print(f"   [CIRCULAR] Found circular no in full page: {metadata['circular_no']}")
                        break
        
        # If still no date found, try URL extraction with more specific patterns
        if metadata["date"] == "Unknown":
            url_date_match = re.search(r'/(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-_]?(\d{4})', url.lower())
            if url_date_match:
                month = url_date_match.group(1).capitalize()
                year = url_date_match.group(2)
                metadata["date"] = f"{month} {year}"
                print(f"   [DATE] Extracted date from URL: {metadata['date']}")
        
        return metadata
        
    except Exception as e:
        print(f"   [WARNING] Error extracting metadata from page: {e}")
        return {"date": "Unknown", "circular_no": "Unknown"}


def scrape_sample_table(base_url: str, download_folder: str = "sample_table_pdfs"):
    """
    Scrape table with id='sample_1', extract links from td > a elements, 
    and download PDFs from those pages.
    """
    # Setup
    download_path = Path(download_folder)
    download_path.mkdir(exist_ok=True)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print(f"🔍 Scraping: {base_url}")
    print(f"📁 Download folder: {download_path.absolute()}")
    
    try:
        # Step 1: Get the main page
        print("\n📄 Fetching main page...")
        resp = session.get(base_url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Step 2: Find table with id="sample_1"
        print("🔎 Looking for table with id='sample_1'...")
        sample_table = soup.find("table", id="sample_1")
        
        if not sample_table:
            print("❌ No table with id='sample_1' found")
            
            # Alternative: check if there's any element with id="sample_1"
            sample_element = soup.find(id="sample_1")
            if sample_element:
                print(f"ℹ️  Found element with id='sample_1' but it's a <{sample_element.name}>, not a table")
                # Look for tables inside this element
                tables_inside = sample_element.find_all("table")
                if tables_inside:
                    print(f"📊 Found {len(tables_inside)} table(s) inside the sample_1 element")
                    sample_table = tables_inside[0]
                    print("✅ Using the first table found")
                else:
                    print("❌ No tables found inside the sample_1 element")
                    return
            else:
                print("❌ No element with id='sample_1' found at all")
                return
        else:
            print("✅ Found table with id='sample_1'")
        
        # Step 3: Extract links from td elements
        print("\n🔗 Extracting links from table cells...")
        td_elements = sample_table.find_all("td")
        print(f"📋 Found {len(td_elements)} table cells (td elements)")
        
        links_to_process = []
        
        for td_idx, td in enumerate(td_elements):
            # Find all a tags within this td
            links = td.find_all("a", href=True)
            
            if links:
                print(f"\n📍 Cell {td_idx + 1}: Found {len(links)} link(s)")
                td_text = td.get_text(strip=True)[:100]
                print(f"   Cell content preview: {td_text}...")
                
                for link in links:
                    href = link["href"]
                    text = link.get_text(strip=True)
                    
                    # Skip javascript links
                    if href.startswith("javascript:"):
                        print(f"   ⏭️  Skipping JavaScript link: {text}")
                        continue
                    
                    # Make full URL
                    full_url = urljoin(base_url, href) if not href.startswith(("http://", "https://")) else href
                    
                    links_to_process.append({
                        "text": text,
                        "url": full_url,
                        "td_index": td_idx,
                        "cell_content": td_text
                    })
                    
                    print(f"   🔗 {text} -> {full_url}")
        
        if not links_to_process:
            print("\n❌ No valid links found in table cells")
            return
        
        print(f"\n📊 Total links to process: {len(links_to_process)}")
        
        # Step 4: Process each link and look for PDFs
        downloaded_files = []
        
        for i, link_info in enumerate(links_to_process, 1):
            url = link_info["url"]
            text = link_info["text"]
            
            print(f"\n🔄 Processing link {i}/{len(links_to_process)}: {text}")
            print(f"   🌐 URL: {url}")
            
            try:
                # Check if the link itself is a PDF
                if url.lower().endswith(".pdf"):
                    print("   📄 Direct PDF link detected")
                    filename = f"direct_{i}_{text[:30]}_{Path(urlparse(url).path).name}"
                    filename = re.sub(r'[^\w\-_.]', '_', filename)  # Sanitize
                    
                    pdf_path = download_pdf(session, url, download_path / filename)
                    if pdf_path:
                        downloaded_files.append(pdf_path)
                else:
                    # Scrape the page for PDF links
                    print("   🔍 Scraping page for PDFs...")
                    pdf_urls = find_pdfs_on_page(session, url)
                    
                    if pdf_urls:
                        print(f"   ✅ Found {len(pdf_urls)} PDF(s) on the page")
                        for j, pdf_url in enumerate(pdf_urls):
                            filename = f"page_{i}_{j+1}_{text[:20]}_{Path(urlparse(pdf_url).path).name}"
                            filename = re.sub(r'[^\w\-_.]', '_', filename)
                            
                            pdf_path = download_pdf(session, pdf_url, download_path / filename)
                            if pdf_path:
                                downloaded_files.append(pdf_path)
                    else:
                        print("   ❌ No PDFs found on this page")
                
                # Be respectful to the server
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing {url}: {e}")
        
        # Step 5: Summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"🔗 Links processed: {len(links_to_process)}")
        print(f"📄 PDFs downloaded: {len(downloaded_files)}")
        print(f"📁 Download location: {download_path.absolute()}")
        
        if downloaded_files:
            print("\n📚 Downloaded files:")
            for pdf_file in downloaded_files:
                print(f"   📖 {pdf_file.name}")
        else:
            print("\n⚠️  No PDFs were downloaded")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")

def find_pdfs_on_page(session: requests.Session, url: str) -> List[str]:
    """Find PDF links on a webpage, including those in iframe src attributes."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        pdf_urls = []
        
        # Method 1: Look for direct PDF links in <a> tags
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if href.lower().endswith(".pdf"):
                full_pdf_url = urljoin(url, href) if not href.startswith(("http://", "https://")) else href
                pdf_urls.append(full_pdf_url)
                print(f"   📄 Found PDF link: {full_pdf_url}")
        
        # Method 2: Look for PDFs in iframe src attributes
        iframes = soup.find_all("iframe", src=True)
        print(f"   🖼️  Found {len(iframes)} iframe(s) on the page")
        
        for iframe in iframes:
            src = iframe["src"]
            print(f"   🔍 Checking iframe src: {src}")
            
            # Check for SEBI-style iframe with file parameter (e.g., ../../../web/?file=PDF_URL)
            if "?file=" in src:
                # Extract the PDF URL from the file parameter
                import urllib.parse
                try:
                    # Handle relative URLs first
                    full_iframe_url = urljoin(url, src) if not src.startswith(("http://", "https://")) else src
                    parsed_src = urllib.parse.urlparse(full_iframe_url)
                    query_params = urllib.parse.parse_qs(parsed_src.query)
                    
                    if 'file' in query_params:
                        pdf_url = query_params['file'][0]
                        print(f"   📄 Extracted PDF from iframe file parameter: {pdf_url}")
                        pdf_urls.append(pdf_url)
                except Exception as e:
                    print(f"   ⚠️  Error parsing iframe src: {e}")
            
            # Check if iframe src is a direct PDF
            elif src.lower().endswith(".pdf"):
                full_pdf_url = urljoin(url, src) if not src.startswith(("http://", "https://")) else src
                pdf_urls.append(full_pdf_url)
                print(f"   📄 Found direct PDF in iframe: {full_pdf_url}")
            
            # Also check if iframe src contains 'pdf' in the URL path
            elif "pdf" in src.lower() or ".pdf" in src.lower():
                full_pdf_url = urljoin(url, src) if not src.startswith(("http://", "https://")) else src
                pdf_urls.append(full_pdf_url)
                print(f"   📄 Found potential PDF in iframe: {full_pdf_url}")
        
        # Method 3: Look for embed tags with PDF sources
        embeds = soup.find_all("embed", src=True)
        for embed in embeds:
            src = embed["src"]
            if src.lower().endswith(".pdf") or "pdf" in src.lower():
                full_pdf_url = urljoin(url, src) if not src.startswith(("http://", "https://")) else src
                pdf_urls.append(full_pdf_url)
                print(f"   📄 Found PDF in embed: {full_pdf_url}")
        
        # Method 4: Look for object tags with PDF data
        objects = soup.find_all("object", data=True)
        for obj in objects:
            data = obj["data"]
            if data.lower().endswith(".pdf") or "pdf" in data.lower():
                full_pdf_url = urljoin(url, data) if not data.startswith(("http://", "https://")) else data
                pdf_urls.append(full_pdf_url)
                print(f"   📄 Found PDF in object: {full_pdf_url}")
        
        # Remove duplicates while preserving order
        unique_pdfs = []
        seen = set()
        for pdf_url in pdf_urls:
            if pdf_url not in seen:
                unique_pdfs.append(pdf_url)
                seen.add(pdf_url)
        
        return unique_pdfs
        
    except Exception as e:
        print(f"   ⚠️  Error scanning page for PDFs: {e}")
        return []

def download_pdf(session: requests.Session, pdf_url: str, filepath: Path) -> Path | None:
    """Download a PDF file."""
    try:
        if filepath.exists():
            print(f"   ℹ️  File already exists: {filepath.name}")
            return filepath
        
        print(f"   📥 Downloading: {filepath.name}")
        resp = session.get(pdf_url, timeout=60)
        resp.raise_for_status()
        
        with open(filepath, "wb") as f:
            f.write(resp.content)
        
        print(f"   ✅ Downloaded: {filepath.name} ({len(resp.content)} bytes)")
        return filepath
        
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return None

def main():
    """Main function with user input."""
    print("🚀 Sample Table PDF Scraper")
    print("="*50)
    
    # Get URL from user
    url = input("Enter the website URL: ").strip()
    if not url:
        url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
        print(f"Using default URL: {url}")
    
    # Get download folder
    folder = input("Enter download folder name (default: sample_table_pdfs): ").strip()
    if not folder:
        folder = "sample_table_pdfs"
    
    scrape_sample_table(url, folder)

if __name__ == "__main__":
    main()
