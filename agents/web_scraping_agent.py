
from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langsmith import traceable

# Import the WorkflowState and utility functions from the shared types module
from workflow_types import WorkflowState, log_message, create_message

# Import the scraping functionality
from tool.webScrapper.ajax_scraper import scrape_page


@traceable(name="web_scraping_agent")
def web_scraping_agent(state: WorkflowState) -> WorkflowState:
    """Web Scraping Agent - Downloads PDFs from SEBI website"""
    agent_name = "Web Scraping Agent"
    log_message(agent_name, "🚀 Starting web scraping process...")
    
    try:
        # Update state
        state["current_stage"] = "web_scraping"
        state["messages"].append(
            create_message(agent_name, "Starting web scraping for SEBI documents")
        )
        
        # Extract parameters from state
        page_numbers = state.get("page_numbers", [1])
        download_folder = state.get("download_folder", "test_enhanced_metadata")
        
        log_message(agent_name, f"Scraping pages: {page_numbers}")
        log_message(agent_name, f"Download folder: {download_folder}")
        
        # Execute scraping
        scraping_result = scrape_page(page_numbers, download_folder)
        
        # Update state with results
        state["scraping_result"] = scraping_result
        state["messages"].append(
            create_message(
                agent_name,
                f"Successfully scraped {scraping_result.get('total_downloaded_files', 0)} files",
                "success"
            )
        )
        
        log_message(agent_name, "✅ Web scraping completed successfully")
        return state
        
    except Exception as e:
        error_msg = f"Web scraping failed: {str(e)}"
        log_message(agent_name, error_msg, "ERROR")
        state["errors"].append(error_msg)
        state["messages"].append(create_message(agent_name, error_msg, "error"))
        return state
