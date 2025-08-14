"""Complete SEBI scraper that downloads PDFs AND generates JSON metadata."""
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from table_scraper_fixed import extract_circular_metadata

def download_pdf(session: requests.Session, pdf_url: str, filepath: Path) -> Path | None:
    """Download a PDF file from the given URL."""
    try:
        print(f"   [DOWNLOAD] Downloading: {filepath.name}")
        resp = session.get(pdf_url, timeout=60, stream=True)
        resp.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = resp.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
            print(f"   [WARNING] URL may not be a PDF (content-type: {content_type})")
        
        # Write the file
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = filepath.stat().st_size
        print(f"   [SUCCESS] Downloaded: {filepath.name} ({file_size} bytes)")
        return filepath
        
    except Exception as e:
        print(f"   [ERROR] Failed to download {pdf_url}: {e}")
        return None

def find_pdfs_on_page(session: requests.Session, url: str) -> list[str]:
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
                print(f"   [PDF] Found PDF link: {full_pdf_url}")
        
        # Method 2: Look for PDFs in iframe src attributes
        iframes = soup.find_all("iframe", src=True)
        print(f"   [IFRAME] Found {len(iframes)} iframe(s) on the page")
        
        for iframe in iframes:
            src = iframe["src"]
            print(f"   [CHECK] Checking iframe src: {src}")
            
            try:
                # Handle relative URLs
                if not src.startswith(("http://", "https://")):
                    src = urljoin(url, src)
                
                # Check if iframe src contains PDF reference
                if "file=" in src.lower() and ".pdf" in src.lower():
                    # Extract PDF URL from file parameter
                    import urllib.parse
                    parsed = urllib.parse.urlparse(src)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    
                    if 'file' in query_params:
                        pdf_file_url = query_params['file'][0]
                        if not pdf_file_url.startswith(("http://", "https://")):
                            pdf_file_url = urljoin("https://www.sebi.gov.in/", pdf_file_url)
                        
                        pdf_urls.append(pdf_file_url)
                        print(f"   [PDF] Extracted PDF from iframe file parameter: {pdf_file_url}")
                
                elif src.lower().endswith(".pdf"):
                    pdf_urls.append(src)
                    print(f"   [PDF] Found PDF iframe: {src}")
                
            except Exception as e:
                print(f"   [ERROR] Error parsing iframe src: {e}")
        
        return pdf_urls
        
    except Exception as e:
        print(f"   [ERROR] Error scanning page for PDFs: {e}")
        return []

def complete_scraper_with_pdfs():
    """Complete scraper that downloads PDFs AND generates metadata."""
    
    base_url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
    download_folder = "sebi_circulars_pdfs"
    
    print("[START] Complete SEBI PDF scraper with metadata")
    print(f"[TARGET] Table with id='sample_1'")
    print(f"[FOLDER] Download folder: {download_folder}")
    print(f"[METADATA] JSON metadata will be saved as: metadata.json")
    print("=" * 60)
    
    # Setup
    download_path = Path(download_folder)
    download_path.mkdir(exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    
    try:
        # Step 1: Get the main page
        print("\n[PAGE] Fetching main page...")
        resp = session.get(base_url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Step 2: Find table with id="sample_1"
        print("[SEARCH] Looking for table with id='sample_1'...")
        sample_table = soup.find("table", id="sample_1")
        
        if not sample_table:
            print("[ERROR] No table with id='sample_1' found")
            return
        else:
            print("[OK] Found table with id='sample_1'")
        
        # Step 3: Extract links from td elements
        print("\n[LINKS] Extracting links from table cells...")
        td_elements = sample_table.find_all("td")
        print(f"[INFO] Found {len(td_elements)} table cells (td elements)")
        
        links_to_process = []
        
        for td_idx, td in enumerate(td_elements):
            # Find all a tags within this td
            links = td.find_all("a", href=True)
            
            if links:
                td_text = td.get_text(strip=True)[:100]
                
                for link in links:
                    href = link["href"]
                    text = link.get_text(strip=True)
                    
                    # Skip javascript links
                    if href.startswith("javascript:"):
                        continue
                    
                    # Make full URL
                    full_url = urljoin(base_url, href) if not href.startswith(("http://", "https://")) else href
                    
                    links_to_process.append({
                        "text": text,
                        "url": full_url,
                        "td_index": td_idx,
                        "cell_content": td_text
                    })
        
        print(f"[STATS] Total links to process: {len(links_to_process)}")
        
        # Step 4: Process each link - extract metadata AND download PDFs
        metadata_list = []
        downloaded_files = []
        
        for i, link_info in enumerate(links_to_process, 1):
            url = link_info["url"]
            text = link_info["text"]
            
            print(f"\n[PROCESS] {i}/{len(links_to_process)}: {text[:50]}...")
            print(f"   [URL] {url}")
            
            # Extract metadata for this link
            print("   [METADATA] Extracting metadata...")
            metadata = extract_circular_metadata(session, url)
            print(f"   [DATE] {metadata['date']}")
            print(f"   [CIRCULAR] {metadata['circular_no']}")
            
            # Find and download PDFs
            print("   [SEARCH] Searching for PDFs...")
            pdf_urls = find_pdfs_on_page(session, url)
            
            if pdf_urls:
                print(f"   [FOUND] Found {len(pdf_urls)} PDF(s) on the page")
                for j, pdf_url in enumerate(pdf_urls):
                    filename = f"page_{i}_{j+1}_{text[:20]}_{Path(urlparse(pdf_url).path).name}"
                    filename = re.sub(r'[^\w\-_.]', '_', filename)
                    
                    # Check if file already exists
                    filepath = download_path / filename
                    if filepath.exists():
                        print(f"   [EXISTS] File already exists: {filename}")
                        # Still add to metadata
                        metadata_entry = {
                            "date": metadata["date"],
                            "circular_no": metadata["circular_no"],
                            "title": text,
                            "pdf_filename": filename,
                            "source_url": url,
                            "pdf_url": pdf_url,
                            "cell_content": link_info["cell_content"],
                            "download_timestamp": datetime.now().isoformat(),
                            "download_status": "already_existed"
                        }
                        metadata_list.append(metadata_entry)
                    else:
                        # Download the file
                        downloaded_path = download_pdf(session, pdf_url, filepath)
                        if downloaded_path:
                            downloaded_files.append(downloaded_path)
                            
                            # Add to metadata
                            metadata_entry = {
                                "date": metadata["date"],
                                "circular_no": metadata["circular_no"],
                                "title": text,
                                "pdf_filename": filename,
                                "source_url": url,
                                "pdf_url": pdf_url,
                                "cell_content": link_info["cell_content"],
                                "download_timestamp": datetime.now().isoformat(),
                                "download_status": "downloaded"
                            }
                            metadata_list.append(metadata_entry)
                        else:
                            # Add to metadata even if download failed
                            metadata_entry = {
                                "date": metadata["date"],
                                "circular_no": metadata["circular_no"],
                                "title": text,
                                "pdf_filename": filename,
                                "source_url": url,
                                "pdf_url": pdf_url,
                                "cell_content": link_info["cell_content"],
                                "download_timestamp": datetime.now().isoformat(),
                                "download_status": "download_failed"
                            }
                            metadata_list.append(metadata_entry)
            else:
                print("   [NO_PDF] No PDFs found on this page")
                # Still add metadata entry without PDF
                metadata_entry = {
                    "date": metadata["date"],
                    "circular_no": metadata["circular_no"],
                    "title": text,
                    "pdf_filename": None,
                    "source_url": url,
                    "pdf_url": None,
                    "cell_content": link_info["cell_content"],
                    "download_timestamp": datetime.now().isoformat(),
                    "download_status": "no_pdf_found"
                }
                metadata_list.append(metadata_entry)
            
            # Be respectful to the server
            time.sleep(1)
        
        # Step 5: Create metadata JSON
        metadata_json = {
            "scraping_info": {
                "base_url": base_url,
                "scraping_timestamp": datetime.now().isoformat(),
                "total_links_processed": len(links_to_process),
                "total_pdfs_found": len([m for m in metadata_list if m["pdf_filename"]]),
                "total_pdfs_downloaded": len(downloaded_files),
                "total_pdfs_already_existed": len([m for m in metadata_list if m.get("download_status") == "already_existed"]),
                "download_folder": str(download_path.absolute())
            },
            "pdfs": metadata_list
        }
        
        # Step 6: Save to base directory
        metadata_file = Path("metadata.json")
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_json, f, indent=2, ensure_ascii=False)
        
        # Step 7: Summary
        print("\n" + "="*60)
        print("[SUMMARY] SCRAPING COMPLETE")
        print("="*60)
        print(f"[STATS] Links processed: {len(links_to_process)}")
        print(f"[STATS] PDFs found: {len([m for m in metadata_list if m['pdf_filename']])}")
        print(f"[STATS] PDFs downloaded: {len(downloaded_files)}")
        print(f"[STATS] PDFs already existed: {len([m for m in metadata_list if m.get('download_status') == 'already_existed'])}")
        print(f"[STATS] Download failures: {len([m for m in metadata_list if m.get('download_status') == 'download_failed'])}")
        print(f"[FOLDER] Download location: {download_path.absolute()}")
        print(f"[METADATA] Metadata file: {metadata_file.absolute()}")
        
        # Show download status summary
        if downloaded_files:
            print(f"\n[NEW_DOWNLOADS] Newly downloaded files:")
            for pdf_file in downloaded_files:
                print(f"   [FILE] {pdf_file.name}")
        
        # Show metadata extraction summary
        successful_dates = len([m for m in metadata_list if m["date"] != "Unknown"])
        successful_circulars = len([m for m in metadata_list if m["circular_no"] != "Unknown"])
        print(f"\n[METADATA] Metadata extraction summary:")
        print(f"   [DATES] Dates extracted: {successful_dates}/{len(metadata_list)}")
        print(f"   [CIRCULARS] Circular numbers extracted: {successful_circulars}/{len(metadata_list)}")
        
    except Exception as e:
        print(f"[ERROR] Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    complete_scraper_with_pdfs()
