"""
SEBI AJAX Scraper - Uses the AJAX endpoint for efficient pagination
Based on the discovered AJAX API: /sebiweb/ajax/home/getnewslistinfo.jsp
"""
from __future__ import annotations

import os
import re
import time
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

class SEBIAjaxScraper:
    def __init__(self, base_url: str = "https://www.sebi.gov.in", download_folder: str = "sebi_ajax_pdfs"):
        self.base_url = base_url
        self.download_path = Path(download_folder)
        self.download_path.mkdir(exist_ok=True)
        
        # Setup session with headers from the curl request
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.sebi.gov.in',
            'Referer': 'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
        
        # AJAX endpoint
        self.ajax_url = f"{self.base_url}/sebiweb/ajax/home/getnewslistinfo.jsp"
        
        # Initialize session with cookies (may need to visit main page first)
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting the main page to get cookies."""
        try:
            print("🔧 Initializing session...")
            main_page_url = f"{self.base_url}/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
            resp = self.session.get(main_page_url, timeout=30)
            resp.raise_for_status()
            print(f"✅ Session initialized with {len(self.session.cookies)} cookies")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize session: {e}")
    
    def _extract_date_and_circular_info(self, url: str, html_content: str = None) -> Dict[str, str]:
        """
        Extract date and circular number from URL and page content.
        
        Args:
            url: The URL of the circular page
            html_content: HTML content of the page (optional, for more detailed extraction)
            
        Returns:
            Dictionary with extracted date and circular information
        """
        import re
        from urllib.parse import urlparse
        
        result = {
            "circular_date": None,
            "circular_number": None,
            "circular_month_year": None
        }
        
        try:
            # Extract date from URL path (e.g., /aug-2025/ or /jul-2025/)
            date_match = re.search(r'/([a-z]{3})-(\d{4})/', url)
            if date_match:
                month_abbr = date_match.group(1)
                year = date_match.group(2)
                result["circular_month_year"] = f"{month_abbr}-{year}"
                
                # Convert month abbreviation to full name
                month_mapping = {
                    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
                    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
                    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'
                }
                full_month = month_mapping.get(month_abbr, month_abbr.title())
                result["circular_month_year_full"] = f"{full_month} {year}"
            
            # Extract circular number from URL (usually at the end, e.g., _96052.html)
            circular_match = re.search(r'_(\d+)\.html$', url)
            if circular_match:
                result["circular_number"] = circular_match.group(1)
            
            # If HTML content is provided, try to extract more detailed date information
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Look for date patterns in the HTML content
                # Common patterns: "dated August 14, 2025", "Date: 14/08/2025", etc.
                text_content = soup.get_text()
                
                # Pattern 1: "dated Month DD, YYYY" or "Date: Month DD, YYYY"
                date_pattern1 = re.search(r'dated?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text_content, re.IGNORECASE)
                if date_pattern1:
                    result["circular_date"] = date_pattern1.group(1)
                
                # Pattern 2: "DD/MM/YYYY" or "DD-MM-YYYY"
                date_pattern2 = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', text_content)
                if date_pattern2 and not result["circular_date"]:
                    result["circular_date"] = date_pattern2.group(1)
                
                # Pattern 3: Look for SEBI circular number patterns
                sebi_circular_pattern = re.search(r'SEBI/[A-Z0-9/\-]+/\d{4}/\d+', text_content)
                if sebi_circular_pattern:
                    result["sebi_circular_ref"] = sebi_circular_pattern.group(0)
                    
        except Exception as e:
            print(f"   ⚠️  Warning: Could not extract date/circular info from {url}: {e}")
        
        return result
    
    def _extract_date_from_table_cell(self, td_element) -> str:
        """
        Extract date from table cell that might contain date information.
        
        Args:
            td_element: BeautifulSoup TD element
            
        Returns:
            Extracted date string or None
        """
        try:
            # Get all text from the cell
            cell_text = td_element.get_text(strip=True)
            
            # Look for date patterns
            import re
            
            # Pattern 1: DD/MM/YYYY or DD-MM-YYYY
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', cell_text)
            if date_match:
                return date_match.group(1)
            
            # Pattern 2: Month DD, YYYY
            date_match2 = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', cell_text)
            if date_match2:
                return date_match2.group(1)
                
            # Pattern 3: DD Month YYYY
            date_match3 = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', cell_text)
            if date_match3:
                return date_match3.group(1)
                
        except Exception as e:
            pass
        
        return None
    
    def _save_metadata_json(self, results: Dict[str, Any], save_to_root: bool = True) -> None:
        """Save metadata JSON file with scraping results."""
        try:
            # Apply link enhancement if both links and files are available
            enhanced_results = results.copy()
            if "links" in results and "files" in results:
                enhanced_results["links"] = self._update_links_with_enhanced_info(
                    results["links"], 
                    results["files"]
                )
                print(f"   🔧 Enhanced {len(enhanced_results['links'])} links with extracted information")
            
            # Add timestamp and additional metadata
            metadata = {
                "scrape_timestamp": datetime.datetime.now().isoformat(),
                "scraper_version": "ajax_v2.0",
                "base_url": self.base_url,
                "ajax_endpoint": self.ajax_url,
                **enhanced_results
            }
            
            # Choose where to save the JSON file
            if save_to_root:
                # Save to workspace root directory
                metadata_file = Path.cwd() / "scraping_metadata.json"
            else:
                # Save to download folder
                metadata_file = self.download_path / "scraping_metadata.json"
            
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Metadata saved to: {metadata_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save metadata JSON: {e}")
    
    def get_page_data(self, page_number: int = 1) -> Optional[str]:
        """
        Get data for a specific page using the AJAX endpoint.
        
        Args:
            page_number: The page number to fetch (1-based)
            
        Returns:
            HTML content of the page or None if failed
        """
        try:
            # Correct pagination mapping discovered through testing:
            # Page 1: next='n', nextValue='0'
            # Page 2: next='y', nextValue='0' 
            # Page 3: next='y', nextValue='1'
            # Page 4: next='y', nextValue='2'
            # etc.
            
            if page_number == 1:
                next_param = 'n'
                next_value = '0'
            else:
                next_param = 'y'
                next_value = str(page_number - 2)  # Page 2 -> nextValue=0, Page 3 -> nextValue=1, etc.
            
            # Prepare POST data based on the curl request
            post_data = {
                'nextValue': 1,
                'next': 'n',
                'search': '',
                'fromDate': '',
                'toDate': '',
                'fromYear': '',
                'toYear': '',
                'deptId': '-1',
                'sid': '1',
                'ssid': '7',
                'smid': '0',
                'ssidhidden': '7',
                'intmid': '-1',
                'sText': 'Legal',
                'ssText': 'Circulars',
                'smText': '',
                'doDirect': page_number - 1
            }
            
            print(f"📡 Fetching page {page_number} via AJAX...")
            
            resp = self.session.post(self.ajax_url, data=post_data, timeout=30)
            resp.raise_for_status()
            
            if resp.text.strip():
                print(f"✅ Successfully fetched page {page_number} ({len(resp.text)} chars)")
                return resp.text
            else:
                print(f"❌ Empty response for page {page_number}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching page {page_number}: {e}")
            return None
    
    def extract_links_from_html(self, html_content: str, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract links from the HTML response.
        
        Args:
            html_content: HTML content from AJAX response
            page_number: Page number for reference
            
        Returns:
            List of link dictionaries
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Look for the table with id="sample_1" or any tables
            tables = soup.find_all("table")
            if not tables:
                print(f"⚠️  No tables found in page {page_number} response")
                return []
            
            print(f"📊 Found {len(tables)} table(s) in page {page_number}")
            
            links_found = []
            
            # Process all tables (not just sample_1 as it might not exist in AJAX response)
            for table_idx, table in enumerate(tables):
                td_elements = table.find_all("td")
                print(f"   Table {table_idx + 1}: {len(td_elements)} cells")
                
                for td_idx, td in enumerate(td_elements):
                    # Extract potential date from this cell
                    cell_date = self._extract_date_from_table_cell(td)
                    
                    links = td.find_all("a", href=True)
                    
                    if links:
                        for link in links:
                            href = link["href"]
                            text = link.get_text(strip=True)
                            
                            # Skip javascript links
                            if href.startswith("javascript:"):
                                continue
                            
                            # Make full URL
                            full_url = urljoin(self.base_url, href) if not href.startswith(("http://", "https://")) else href
                            
                            # Extract date and circular information
                            circular_info = self._extract_date_and_circular_info(full_url)
                            
                            # Use cell date if no date found in URL
                            if cell_date and not circular_info["circular_date"]:
                                circular_info["circular_date"] = cell_date
                            
                            link_data = {
                                "text": text,
                                "url": full_url,
                                "page": page_number,
                                "table_index": table_idx,
                                "td_index": td_idx,
                                "cell_content": td.get_text(strip=True)[:100],
                                **circular_info  # Include all circular information
                            }
                            
                            links_found.append(link_data)
            
            print(f"🔗 Extracted {len(links_found)} links from page {page_number}")
            return links_found
            
        except Exception as e:
            print(f"❌ Error extracting links from page {page_number}: {e}")
            return []
    
    def find_pdfs_on_page(self, url: str) -> List[str]:
        """Find PDF links on a webpage, including those in iframe src attributes."""
        try:
            resp = self.session.get(url, timeout=30)
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
                
                # Check for SEBI-style iframe with file parameter
                if "?file=" in src:
                    import urllib.parse
                    try:
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
            
            # Method 3: Look for embed and object tags
            for tag in soup.find_all(["embed", "object"]):
                src_attr = "src" if tag.name == "embed" else "data"
                if tag.has_attr(src_attr):
                    src = tag[src_attr]
                    if src.lower().endswith(".pdf") or "pdf" in src.lower():
                        full_pdf_url = urljoin(url, src) if not src.startswith(("http://", "https://")) else src
                        pdf_urls.append(full_pdf_url)
                        print(f"   📄 Found PDF in {tag.name}: {full_pdf_url}")
            
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
    
    def extract_circular_details_from_page(self, url: str) -> Dict[str, str]:
        """
        Extract circular number and date from the page content, specifically from div with class 'm_section bottom_space2'.
        
        Args:
            url: The URL of the circular page
            
        Returns:
            Dictionary with extracted circular details
        """
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            circular_details = {
                "page_circular_number": None,
                "page_circular_date": None,
                "sebi_circular_ref": None,
                "has_iframe": False
            }
            
            # Check if page has iframe (indicator of PDF content)
            iframes = soup.find_all("iframe")
            circular_details["has_iframe"] = len(iframes) > 0
            
            # Look for the specific div with class 'm_section bottom_space2'
            target_div = soup.find("div", class_="m_section bottom_space2")
            
            if target_div:
                print(f"   📋 Found target div 'm_section bottom_space2'")
                div_text = target_div.get_text(strip=True)
                
                # Extract various patterns from the div text
                import re
                
                # Pattern 1: Look for SEBI circular references with flexible patterns
                # Handle various formats including spaces: "SEBI/HO/MIRSD/ MIRSD-PoD/P/CIR/2025/116"
                sebi_ref_patterns = [
                    r'SEBI/HO/[^/]+/\s*[^/]+/[^/]+/[^/]+/\d{4}/\d+',  # Flexible HO pattern with spaces
                    r'SEBI/[A-Z0-9]+/[^/]+/\s*[^/]+/[^/]+/[^/]+/\d{4}/\d+',  # General office pattern
                    r'SEBI/[^|]+/\d{4}/\d+',  # Very general pattern ending with year/number
                ]
                
                sebi_ref_found = None
                for pattern in sebi_ref_patterns:
                    sebi_ref_match = re.search(pattern, div_text)
                    if sebi_ref_match:
                        found = sebi_ref_match.group(0).strip()
                        # Validate it looks like a proper SEBI reference
                        if re.search(r'SEBI/.+/\d{4}/\d+$', found):
                            # Clean up by removing extra spaces after slashes
                            sebi_ref_found = re.sub(r'/\s+', '/', found)
                            break
                
                if sebi_ref_found:
                    circular_details["sebi_circular_ref"] = sebi_ref_found
                    print(f"   📋 Found SEBI reference: {sebi_ref_found}")
                
                # Pattern 2: Look for circular numbers (usually at the end)
                circular_num_pattern = re.search(r'(?:Circular\s*(?:No\.?|Number)\s*:?\s*)?(\d+)', div_text, re.IGNORECASE)
                if circular_num_pattern:
                    circular_details["page_circular_number"] = circular_num_pattern.group(1)
                    print(f"   🔢 Found circular number: {circular_num_pattern.group(1)}")
                
                # Pattern 3: Look for dates in various formats
                # Format: "August 14, 2025" or "14 August 2025"
                date_pattern1 = re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', div_text)
                if date_pattern1:
                    circular_details["page_circular_date"] = date_pattern1.group(1)
                    print(f"   📅 Found date (format 1): {date_pattern1.group(1)}")
                
                # Format: "14/08/2025" or "14-08-2025" 
                if not circular_details["page_circular_date"]:
                    date_pattern2 = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', div_text)
                    if date_pattern2:
                        circular_details["page_circular_date"] = date_pattern2.group(1)
                        print(f"   📅 Found date (format 2): {date_pattern2.group(1)}")
                
                # Format: Look for "dated" followed by date
                if not circular_details["page_circular_date"]:
                    dated_pattern = re.search(r'dated\s+([^,.\n]+)', div_text, re.IGNORECASE)
                    if dated_pattern:
                        circular_details["page_circular_date"] = dated_pattern.group(1).strip()
                        print(f"   📅 Found date (dated format): {dated_pattern.group(1).strip()}")
                
                print(f"   📄 Div content preview: {div_text[:200]}...")
            else:
                # If specific div not found, search the entire page content
                print(f"   ⚠️  Specific div not found, searching entire page content")
                page_text = soup.get_text()
                
                import re
                
                # Look for SEBI circular references with flexible patterns
                sebi_ref_patterns = [
                    r'SEBI/HO/[^/]+/\s*[^/]+/[^/]+/[^/]+/\d{4}/\d+',  # Flexible HO pattern with spaces
                    r'SEBI/[A-Z0-9]+/[^/]+/\s*[^/]+/[^/]+/[^/]+/\d{4}/\d+',  # General office pattern
                    r'SEBI/[^|]+/\d{4}/\d+',  # Very general pattern ending with year/number
                ]
                
                sebi_ref_found = None
                for pattern in sebi_ref_patterns:
                    sebi_ref_match = re.search(pattern, page_text)
                    if sebi_ref_match:
                        found = sebi_ref_match.group(0).strip()
                        # Validate it looks like a proper SEBI reference
                        if re.search(r'SEBI/.+/\d{4}/\d+$', found):
                            # Clean up by removing extra spaces after slashes
                            sebi_ref_found = re.sub(r'/\s+', '/', found)
                            break
                
                if sebi_ref_found:
                    circular_details["sebi_circular_ref"] = sebi_ref_found
                    print(f"   📋 Found SEBI reference in page: {sebi_ref_found}")
                
                # Look for dates
                date_pattern = re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', page_text)
                if date_pattern:
                    circular_details["page_circular_date"] = date_pattern.group(1)
                    print(f"   📅 Found date in page: {date_pattern.group(1)}")
            
            return circular_details
            
        except Exception as e:
            print(f"   ⚠️  Error extracting circular details from page: {e}")
            return {
                "page_circular_number": None,
                "page_circular_date": None,
                "sebi_circular_ref": None,
                "has_iframe": False
            }
    
    def _update_links_with_enhanced_info(self, links: List[Dict[str, Any]], downloaded_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update links with enhanced information from downloaded files."""
        try:
            # Create a mapping from URL to enhanced info
            url_to_enhanced_info = {}
            
            for file_info in downloaded_files:
                if isinstance(file_info, dict) and "source_url" in file_info:
                    source_url = file_info["source_url"]
                    
                    # Extract enhanced circular information
                    enhanced_info = {
                        "circular_date": file_info.get("circular_date"),
                        "sebi_circular_ref": file_info.get("sebi_circular_ref"),
                        "has_iframe": file_info.get("has_iframe", False),
                        "downloaded_filename": file_info.get("original_filename"),
                        "pdf_url": file_info.get("pdf_url"),
                    }
                    
                    # Use SEBI reference as primary circular number if available
                    if file_info.get("sebi_circular_ref"):
                        enhanced_info["circular_number"] = file_info.get("sebi_circular_ref")
                        enhanced_info["url_circular_id"] = file_info.get("url_circular_id") or file_info.get("circular_number")
                    
                    url_to_enhanced_info[source_url] = enhanced_info
            
            # Update each link with enhanced information
            updated_links = []
            for link in links:
                link_url = link.get("url", "")
                
                if link_url in url_to_enhanced_info:
                    # Create updated link with enhanced info
                    updated_link = {**link}  # Copy original link
                    enhanced_info = url_to_enhanced_info[link_url]
                    
                    # Update with enhanced information
                    for key, value in enhanced_info.items():
                        if value is not None:  # Only update if we have a value
                            updated_link[key] = value
                    
                    updated_links.append(updated_link)
                else:
                    # Keep original link if no enhanced info available
                    updated_links.append(link)
            
            return updated_links
            
        except Exception as e:
            print(f"⚠️  Warning: Could not update links with enhanced info: {e}")
            return links  # Return original links if update fails
    
    def download_pdf(self, pdf_url: str, filename: str) -> Optional[Path]:
        """Download a PDF file."""
        try:
            filepath = self.download_path / filename
            
            if filepath.exists():
                print(f"   ℹ️  File already exists: {filepath.name}")
                return filepath
            
            print(f"   📥 Downloading: {filepath.name}")
            resp = self.session.get(pdf_url, timeout=60)
            resp.raise_for_status()
            
            # Check if the response is actually a PDF
            content_type = resp.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
                # Check if content starts with PDF signature
                if not resp.content.startswith(b'%PDF'):
                    print(f"   ⚠️  Warning: Response doesn't appear to be a PDF (Content-Type: {content_type})")
                    return None
            
            with open(filepath, "wb") as f:
                f.write(resp.content)
            
            print(f"   ✅ Downloaded: {filepath.name} ({len(resp.content)} bytes)")
            return filepath
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return None
    
    def scrape_multiple_pages(self, max_pages: int = 10, start_page: int = 1) -> Dict[str, Any]:
        """
        Scrape multiple pages using the AJAX endpoint.
        
        Args:
            max_pages: Maximum number of pages to scrape
            start_page: Starting page number (1-based)
            
        Returns:
            Dictionary with scraping results
        """
        print(f"🚀 Starting AJAX scraper for {max_pages} pages")
        print(f"📁 Download folder: {self.download_path.absolute()}")
        print(f"📡 AJAX endpoint: {self.ajax_url}")
        
        all_links = []
        downloaded_files = []
        failed_pages = []
        
        for page_num in range(start_page, start_page + max_pages):
            print(f"\n{'='*20} PAGE {page_num} {'='*20}")
            
            # Get page data via AJAX
            html_content = self.get_page_data(page_num)
            
            if not html_content:
                failed_pages.append(page_num)
                print(f"❌ Failed to get data for page {page_num}")
                continue
            
            # Extract links from the HTML
            page_links = self.extract_links_from_html(html_content, page_num)
            
            if not page_links:
                print(f"⚠️  No links found on page {page_num} - might be end of data")
                break
            
            all_links.extend(page_links)
            
            # Process each link for PDFs
            for i, link_info in enumerate(page_links, 1):
                url = link_info["url"]
                text = link_info["text"]
                
                print(f"\n🔄 Processing link {i}/{len(page_links)}: {text[:50]}...")
                print(f"   🌐 URL: {url}")
                
                try:
                    # Check if the link itself is a PDF
                    if url.lower().endswith(".pdf"):
                        print("   📄 Direct PDF link detected")
                        filename = f"page_{page_num}_direct_{i}_{text[:20]}.pdf"
                        filename = re.sub(r'[^\w\-_.]', '_', filename)
                        
                        pdf_path = self.download_pdf(url, filename)
                        if pdf_path:
                            # Create enhanced file info with circular details
                            file_info = {
                                "file_path": str(pdf_path),
                                "original_filename": filename,
                                "source_url": url,
                                "source_page": page_num,
                                "link_text": text,
                                "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                                **link_info  # Include all circular information
                            }
                            downloaded_files.append(file_info)
                    else:
                        # Scrape the page for PDFs
                        print("   🔍 Scraping page for PDFs...")
                        pdf_urls = self.find_pdfs_on_page(url)
                        
                        # Extract detailed circular information from the page content
                        print("   📋 Extracting circular details from page content...")
                        page_circular_details = self.extract_circular_details_from_page(url)
                        
                        # Merge page details with URL-based details
                        enhanced_link_info = {**link_info}
                        
                        # Override with page-extracted details if available
                        if page_circular_details.get("page_circular_date"):
                            enhanced_link_info["circular_date"] = page_circular_details["page_circular_date"]
                        if page_circular_details.get("sebi_circular_ref"):
                            # Use the full SEBI reference as the primary circular number
                            enhanced_link_info["circular_number"] = page_circular_details["sebi_circular_ref"]
                            enhanced_link_info["sebi_circular_ref"] = page_circular_details["sebi_circular_ref"]
                            enhanced_link_info["url_circular_id"] = enhanced_link_info.get("circular_number")  # Keep URL ID as fallback
                        elif page_circular_details.get("page_circular_number"):
                            enhanced_link_info["page_circular_number"] = page_circular_details["page_circular_number"]
                        
                        enhanced_link_info["has_iframe"] = page_circular_details["has_iframe"]
                        
                        if pdf_urls:
                            print(f"   ✅ Found {len(pdf_urls)} PDF(s) on the page")
                            for j, pdf_url in enumerate(pdf_urls):
                                filename = f"page_{page_num}_{i}_{j+1}_{text[:20]}.pdf"
                                filename = re.sub(r'[^\w\-_.]', '_', filename)
                                
                                pdf_path = self.download_pdf(pdf_url, filename)
                                if pdf_path:
                                    # Create enhanced file info with circular details
                                    file_info = {
                                        "file_path": str(pdf_path),
                                        "original_filename": filename,
                                        "source_url": url,
                                        "pdf_url": pdf_url,
                                        "source_page": page_num,
                                        "link_text": text,
                                        "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                                        **enhanced_link_info  # Include all enhanced circular information
                                    }
                                    downloaded_files.append(file_info)
                        else:
                            print("   ❌ No PDFs found on this page")
                    
                    # Be respectful to the server
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Error processing {url}: {e}")
            
            # Small delay between pages
            time.sleep(2)
        
        # Results summary
        results = {
            "pages_processed": max_pages,
            "failed_pages": failed_pages,
            "total_links": len(all_links),
            "downloaded_files": len(downloaded_files),
            "download_path": str(self.download_path.absolute()),
            "links": all_links,
            "files": downloaded_files,  # Now contains detailed file info instead of just paths
            "file_paths": [f["file_path"] if isinstance(f, dict) else str(f) for f in downloaded_files]  # Backward compatibility
        }
        
        # Save metadata JSON file
        self._save_metadata_json(results)
        
        print("\n" + "="*60)
        print("📊 AJAX SCRAPING SUMMARY")
        print("="*60)
        print(f"📄 Pages processed: {max_pages}")
        print(f"❌ Failed pages: {len(failed_pages)}")
        print(f"🔗 Total links found: {len(all_links)}")
        print(f"📄 PDFs downloaded: {len(downloaded_files)}")
        print(f"📁 Download location: {self.download_path.absolute()}")
        
        if failed_pages:
            print(f"\n⚠️  Failed pages: {failed_pages}")
        
        if downloaded_files:
            print(f"\n📚 Sample downloaded files:")
            for i, file_info in enumerate(downloaded_files[:5]):  # Show first 5
                if isinstance(file_info, dict):
                    filename = file_info.get("original_filename", "unknown")
                    # Prioritize full SEBI reference over other circular numbers
                    circular_no = (file_info.get("sebi_circular_ref") or 
                                 file_info.get("page_circular_number") or 
                                 file_info.get("circular_number", "N/A"))
                    date = file_info.get("circular_date", "N/A")
                    has_iframe = file_info.get("has_iframe", False)
                    iframe_indicator = "🖼️ " if has_iframe else ""
                    print(f"   📖 {iframe_indicator}{filename}")
                    print(f"       � Circular: {circular_no}")
                    print(f"       📅 Date: {date}")
                else:
                    print(f"   📖 {file_info}")  # Fallback for old format
            if len(downloaded_files) > 5:
                print(f"   ... and {len(downloaded_files) - 5} more files")
        else:
            print("\n⚠️  No PDFs were downloaded")
        
        return results
    
    def scrape_single_page(self, page_number: int) -> Dict[str, Any]:
        """
        Scrape a single specific page by page number.
        
        Args:
            page_number: The specific page number to scrape (1-based)
            
        Returns:
            Dictionary with scraping results for that page
        """
        print(f"🎯 Scraping single page: {page_number}")
        print(f"📁 Download folder: {self.download_path.absolute()}")
        print(f"📡 AJAX endpoint: {self.ajax_url}")
        
        # Get page data via AJAX
        html_content = self.get_page_data(page_number)
        
        if not html_content:
            return {
                "page_number": page_number,
                "success": False,
                "error": "Failed to fetch page data",
                "links": [],
                "downloaded_files": 0,
                "files": []
            }
        
        # Extract links from the HTML
        page_links = self.extract_links_from_html(html_content, page_number)
        
        if not page_links:
            return {
                "page_number": page_number,
                "success": False,
                "error": "No links found on page",
                "links": [],
                "downloaded_files": 0,
                "files": []
            }
        
        print(f"🔗 Found {len(page_links)} links on page {page_number}")
        
        downloaded_files = []
        
        # Process each link for PDFs
        for i, link_info in enumerate(page_links, 1):
            url = link_info["url"]
            text = link_info["text"]
            
            print(f"\n🔄 Processing link {i}/{len(page_links)}: {text[:50]}...")
            print(f"   🌐 URL: {url}")
            
            try:
                # Check if the link itself is a PDF
                if url.lower().endswith(".pdf"):
                    print("   📄 Direct PDF link detected")
                    filename = f"page_{page_number}_direct_{i}_{text[:20]}.pdf"
                    filename = re.sub(r'[^\w\-_.]', '_', filename)
                    
                    pdf_path = self.download_pdf(url, filename)
                    if pdf_path:
                        # Create enhanced file info with circular details
                        file_info = {
                            "file_path": str(pdf_path),
                            "original_filename": filename,
                            "source_url": url,
                            "source_page": page_number,
                            "link_text": text,
                            "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                            **link_info  # Include all circular information
                        }
                        downloaded_files.append(file_info)
                else:
                    # Scrape the page for PDF links
                    print("   🔍 Scraping page for PDFs...")
                    pdf_urls = self.find_pdfs_on_page(url)
                    
                    # Extract detailed circular information from the page content
                    print("   📋 Extracting circular details from page content...")
                    page_circular_details = self.extract_circular_details_from_page(url)
                    
                    # Merge page details with URL-based details
                    enhanced_link_info = {**link_info}
                    
                    # Override with page-extracted details if available
                    if page_circular_details.get("page_circular_date"):
                        enhanced_link_info["circular_date"] = page_circular_details["page_circular_date"]
                    if page_circular_details.get("sebi_circular_ref"):
                        # Use the full SEBI reference as the primary circular number
                        enhanced_link_info["circular_number"] = page_circular_details["sebi_circular_ref"]
                        enhanced_link_info["sebi_circular_ref"] = page_circular_details["sebi_circular_ref"]
                        enhanced_link_info["url_circular_id"] = enhanced_link_info.get("circular_number")  # Keep URL ID as fallback
                    elif page_circular_details.get("page_circular_number"):
                        enhanced_link_info["page_circular_number"] = page_circular_details["page_circular_number"]
                    
                    enhanced_link_info["has_iframe"] = page_circular_details["has_iframe"]
                    
                    if pdf_urls:
                        print(f"   ✅ Found {len(pdf_urls)} PDF(s) on the page")
                        for j, pdf_url in enumerate(pdf_urls):
                            filename = f"page_{page_number}_{i}_{j+1}_{text[:20]}.pdf"
                            filename = re.sub(r'[^\w\-_.]', '_', filename)
                            
                            pdf_path = self.download_pdf(pdf_url, filename)
                            if pdf_path:
                                # Create enhanced file info with circular details
                                file_info = {
                                    "file_path": str(pdf_path),
                                    "original_filename": filename,
                                    "source_url": url,
                                    "pdf_url": pdf_url,
                                    "source_page": page_number,
                                    "link_text": text,
                                    "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
                                    **enhanced_link_info  # Include all enhanced circular information
                                }
                                downloaded_files.append(file_info)
                    else:
                        print("   ❌ No PDFs found on this page")
                
                # Be respectful to the server
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error processing {url}: {e}")
        
        # Results summary
        results = {
            "page_number": page_number,
            "success": True,
            "links_found": len(page_links),
            "downloaded_files": len(downloaded_files),
            "download_path": str(self.download_path.absolute()),
            "links": page_links,
            "files": downloaded_files,  # Now contains detailed file info instead of just paths
            "file_paths": [f["file_path"] if isinstance(f, dict) else str(f) for f in downloaded_files]  # Backward compatibility
        }
        
        # Save metadata JSON file
        self._save_metadata_json(results)
        
        print(f"\n📊 PAGE {page_number} SUMMARY:")
        print(f"🔗 Links found: {len(page_links)}")
        print(f"📄 PDFs downloaded: {len(downloaded_files)}")
        
        if downloaded_files:
            print(f"📚 Downloaded files:")
            for file_info in downloaded_files:
                if isinstance(file_info, dict):
                    filename = file_info.get("original_filename", "unknown")
                    # Prioritize full SEBI reference over other circular numbers
                    circular_no = (file_info.get("sebi_circular_ref") or 
                                 file_info.get("page_circular_number") or 
                                 file_info.get("circular_number", "N/A"))
                    date = file_info.get("circular_date", "N/A")
                    has_iframe = file_info.get("has_iframe", False)
                    iframe_indicator = "🖼️ " if has_iframe else ""
                    print(f"   📖 {iframe_indicator}{filename}")
                    print(f"       � Circular: {circular_no}")
                    print(f"       📅 Date: {date}")
                else:
                    print(f"   📖 {file_info}")  # Fallback for old format
        
        return results
    
    def scrape_specific_pages(self, page_numbers: List[int]) -> Dict[str, Any]:
        """
        Scrape specific page numbers.
        
        Args:
            page_numbers: List of page numbers to scrape (1-based)
            
        Returns:
            Dictionary with combined scraping results
        """
        print(f"🎯 Scraping specific pages: {page_numbers}")
        print(f"📁 Download folder: {self.download_path.absolute()}")
        
        all_results = []
        all_links = []
        all_downloaded_files = []
        failed_pages = []
        
        for page_num in page_numbers:
            print(f"\n{'='*20} PAGE {page_num} {'='*20}")
            
            try:
                page_result = self.scrape_single_page(page_num)
                all_results.append(page_result)
                
                if page_result["success"]:
                    all_links.extend(page_result["links"])
                    # Handle both old and new file formats
                    page_files = page_result.get("files", [])
                    if isinstance(page_files, list) and page_files:
                        if isinstance(page_files[0], dict):
                            all_downloaded_files.extend(page_files)
                        else:
                            # Convert old format to new format for consistency
                            for file_path in page_files:
                                all_downloaded_files.append({"file_path": str(file_path)})
                else:
                    failed_pages.append(page_num)
                    
            except Exception as e:
                print(f"❌ Error scraping page {page_num}: {e}")
                failed_pages.append(page_num)
        
        # Combined results
        combined_results = {
            "pages_requested": page_numbers,
            "pages_processed": len([r for r in all_results if r["success"]]),
            "failed_pages": failed_pages,
            "total_links": len(all_links),
            "total_downloaded_files": len(all_downloaded_files),
            "download_path": str(self.download_path.absolute()),
            "page_results": all_results,
            "all_links": all_links,
            "all_files": all_downloaded_files,  # Now contains detailed file info
            "all_file_paths": [f["file_path"] if isinstance(f, dict) else str(f) for f in all_downloaded_files]  # Backward compatibility
        }
        
        # Save metadata JSON file
        self._save_metadata_json(combined_results)
        
        print("\n" + "="*60)
        print("📊 SPECIFIC PAGES SCRAPING SUMMARY")
        print("="*60)
        print(f"📄 Pages requested: {page_numbers}")
        print(f"✅ Pages successfully processed: {len([r for r in all_results if r['success']])}")
        print(f"❌ Failed pages: {failed_pages}")
        print(f"🔗 Total links found: {len(all_links)}")
        print(f"📄 Total PDFs downloaded: {len(all_downloaded_files)}")
        print(f"📁 Download location: {self.download_path.absolute()}")
        
        return combined_results

# Dynamic functions that can be called directly
def scrape_page(page_numbers, download_folder: str = "sebi_single_page") -> Dict[str, Any]:
    """
    Dynamic function to scrape multiple pages by number.
    
    Args:
        page_numbers: Page number(s) to scrape - can be int for single page or list for multiple pages
        download_folder: Folder to save PDFs
        
    Returns:
        Dictionary with scraping results
    
    Example:
        results = scrape_page(5, "page_5_pdfs")  # Single page
        results = scrape_page([1, 2, 5, 10], "multiple_pages_pdfs")  # Multiple pages
    """
    scraper = SEBIAjaxScraper(download_folder=download_folder)
    
    # Handle both single page number and array of page numbers
    if isinstance(page_numbers, int):
        results = scraper.scrape_single_page(page_numbers)
    elif isinstance(page_numbers, list):
        results = scraper.scrape_specific_pages(page_numbers)
    else:
        raise ValueError("page_numbers must be either an int or a list of ints")
    
    # Ensure metadata is saved for dynamic function calls too
    try:
        metadata_file = Path(download_folder) / "scraping_metadata.json"
        if not metadata_file.exists():
            scraper._save_metadata_json(results)
    except Exception as e:
        print(f"⚠️  Note: Metadata may not have been saved: {e}")
    
    return results

def scrape_pages(page_numbers: List[int], download_folder: str = "sebi_multiple_pages") -> Dict[str, Any]:
    """
    Dynamic function to scrape multiple specific pages.
    
    Args:
        page_numbers: List of page numbers to scrape (1-based)
        download_folder: Folder to save PDFs
        
    Returns:
        Dictionary with combined scraping results
    
    Example:
        results = scrape_pages([1, 3, 5, 10], "selected_pages_pdfs")
    """
    scraper = SEBIAjaxScraper(download_folder=download_folder)
    results = scraper.scrape_specific_pages(page_numbers)
    
    # Ensure metadata is saved for dynamic function calls too
    try:
        metadata_file = Path(download_folder) / "scraping_metadata.json"
        if not metadata_file.exists():
            scraper._save_metadata_json(results)
    except Exception as e:
        print(f"⚠️  Note: Metadata may not have been saved: {e}")
    
    return results

def get_page_links_only(page_number: int) -> List[Dict[str, Any]]:
    """
    Get only the links from a specific page without downloading PDFs.
    
    Args:
        page_number: Page number to get links from (1-based)
        
    Returns:
        List of link dictionaries
    
    Example:
        links = get_page_links_only(7)
    """
    scraper = SEBIAjaxScraper(download_folder="temp_links_only")
    html_content = scraper.get_page_data(page_number)
    
    if html_content:
        return scraper.extract_links_from_html(html_content, page_number)
    else:
        return []

def main():
    """Main function for testing the AJAX scraper."""
    print("🚀 SEBI AJAX PDF Scraper")
    print("="*50)
    
    # Get parameters from user
    max_pages = input("Enter max pages to scrape (default: 5): ").strip()
    max_pages = int(max_pages) if max_pages.isdigit() else 5
    
    folder = input("Enter download folder name (default: sebi_ajax_pdfs): ").strip()
    folder = folder if folder else "sebi_ajax_pdfs"
    
    # Create scraper and run
    scraper = SEBIAjaxScraper(download_folder=folder)
    results = scraper.scrape_multiple_pages(max_pages=max_pages)
    
    # Save results to JSON
    results_file = Path(folder) / "scraping_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
