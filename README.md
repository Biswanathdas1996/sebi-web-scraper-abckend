# SEBI AJAX PDF Scraper

An efficient AJAX-based scraper for downloading PDFs from SEBI (Securities and Exchange Board of India) circulars website. Uses the AJAX endpoint for fast pagination and comprehensive PDF extraction with enhanced metadata.

## Features

- **AJAX-based scraping** for efficient pagination
- **Dynamic functions** for flexible page selection  
- **Enhanced metadata extraction** with dates and circular numbers
- **PDF detection** from multiple sources (links, iframes, embeds)
- **Respectful scraping** with appropriate delays
- **Comprehensive logging** and error handling
- **JSON metadata export** for integration with other tools

## Setup

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## Quick Usage

### Scrape a single page
```python
from ajax_scraper import scrape_page

result = scrape_page(page_number=5, download_folder="page_5_pdfs")
print(f"Downloaded {result['downloaded_files']} PDFs from page 5")
```

### Scrape multiple specific pages
```python
from ajax_scraper import scrape_pages

results = scrape_pages(page_numbers=[1, 3, 5, 10], download_folder="selected_pages")
print(f"Total PDFs downloaded: {results['total_downloaded_files']}")
```

### Get links without downloading
```python
from ajax_scraper import get_page_links_only

links = get_page_links_only(page_number=7)
print(f"Found {len(links)} links on page 7")
```

## Run Examples

### Pre-configured Scraper
```powershell
python run_ajax_scraper.py
```

### Direct Usage
```powershell
python ajax_scraper.py
```

## Documentation

See `DYNAMIC_SCRAPER_GUIDE.md` for detailed usage examples and API reference.

## Output

- **PDFs**: Downloaded to specified folder
- **Metadata**: `scraping_metadata.json` with comprehensive extraction details
- **Logs**: Detailed console output with progress indicators
