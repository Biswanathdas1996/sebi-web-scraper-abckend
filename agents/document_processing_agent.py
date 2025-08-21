# Import necessary modules and dependencies
from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langsmith import traceable

# Import the WorkflowState and utility functions from the shared types module
from workflow_types import WorkflowState, log_message, create_message

# Import the document processing functionality
from tool.fileReader.index import process_test_enhanced_metadata_pdfs, process_documents_for_workflow
# Import docling processor for enhanced document processing
try:
    from tool.fileReader.docling_processor import process_test_enhanced_metadata_with_docling
    DOCLING_AVAILABLE = True
    print("✅ Docling processor available for workflow")
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️  Docling processor not available, using standard methods")


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
        
        # Execute enhanced document processing optimized for workflow
        log_message(agent_name, "🚀 Starting enhanced document processing with docling integration")
        processing_result = process_documents_for_workflow()
        
        # Update state with results
        state["processing_result"] = processing_result
        
        if processing_result and "pdf_processing" in processing_result:
            processed_count = processing_result["pdf_processing"].get("processed_files_count", 0)
            total_count = processing_result["pdf_processing"].get("total_pdf_files", 0)
            processing_method = processing_result["pdf_processing"].get("processing_method", "standard")
            
            # Enhanced statistics for docling processing
            if "processing_stats" in processing_result["pdf_processing"]:
                stats = processing_result["pdf_processing"]["processing_stats"]
                docling_successes = stats.get("docling_successes", 0)
                fallback_used = stats.get("fallback_used", 0)
                
                if docling_successes > 0:
                    state["messages"].append(
                        create_message(
                            agent_name,
                            f"✅ Enhanced processing: {processed_count}/{total_count} files (🚀 {docling_successes} with docling, 🔄 {fallback_used} with fallback)",
                            "success"
                        )
                    )
                else:
                    state["messages"].append(
                        create_message(
                            agent_name,
                            f"✅ Standard processing: {processed_count}/{total_count} files using {processing_method}",
                            "success"
                        )
                    )
            else:
                state["messages"].append(
                    create_message(
                        agent_name,
                        f"Successfully processed {processed_count}/{total_count} PDF files using {processing_method}",
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
