# Import necessary modules and dependencies
from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langsmith import traceable

# Import the WorkflowState and utility functions from the shared types module
from workflow_types import WorkflowState, log_message, create_message

# Import the document processing functionality
from tool.fileReader.index import process_test_enhanced_metadata_pdfs


@traceable(name="document_processing_agent")
def document_processing_agent(state: WorkflowState) -> WorkflowState:
    """Document Processing Agent - Extracts text from downloaded PDFs"""
    agent_name = "Document Processing Agent"
    log_message(agent_name, "📄 Starting document processing...")
    
    try:
        # Update state
        state["current_stage"] = "document_processing"
        state["messages"].append(
            create_message(agent_name, "Starting PDF text extraction")
        )
        
        # Check if we have files to process
        scraping_result = state.get("scraping_result", {})
        if not scraping_result or scraping_result.get("total_downloaded_files", 0) == 0:
            raise Exception("No files were downloaded in the scraping stage")
        
        log_message(agent_name, f"Processing {scraping_result.get('total_downloaded_files')} PDF files")
        
        # Execute document processing
        processing_result = process_test_enhanced_metadata_pdfs()
        
        # Update state with results
        state["processing_result"] = processing_result
        
        if processing_result and "pdf_processing" in processing_result:
            processed_count = processing_result["pdf_processing"].get("processed_files_count", 0)
            state["messages"].append(
                create_message(
                    agent_name,
                    f"Successfully processed {processed_count} PDF files",
                    "success"
                )
            )
        else:
            state["messages"].append(
                create_message(agent_name, "Document processing completed", "success")
            )
        
        log_message(agent_name, "✅ Document processing completed successfully")
        return state
        
    except Exception as e:
        error_msg = f"Document processing failed: {str(e)}"
        log_message(agent_name, error_msg, "ERROR")
        state["errors"].append(error_msg)
        state["messages"].append(create_message(agent_name, error_msg, "error"))
        return state
