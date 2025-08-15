import asyncio
import json
import os
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# LangSmith tracing setup
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from langsmith_config import configure_langsmith, validate_langsmith_setup

# Initialize LangSmith configuration
print("🔧 Initializing LangSmith configuration...")
is_valid, issues = validate_langsmith_setup()
if is_valid:
    configure_langsmith()
else:
    print("⚠️  LangSmith configuration issues detected:")
    for issue in issues:
        print(f"   • {issue}")
    print("   Workflow will continue but tracing may not work properly.")

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

# Import our existing tools
from tool.webScrapper.ajax_scraper import scrape_page
from tool.fileReader.index import process_test_enhanced_metadata_pdfs
from tool.classiflire.index import run_analysis

# State definition for the workflow
class WorkflowState(TypedDict):
    """State that gets passed between agents in the workflow"""
    # Input parameters
    page_numbers: List[int]
    download_folder: str
    
    # Results from each stage
    scraping_result: Dict[str, Any]
    processing_result: Dict[str, Any]
    analysis_result: Dict[str, Any]
    
    # Workflow metadata
    current_stage: str
    workflow_id: str
    start_time: str
    errors: List[str]
    
    # Messages for agent communication
    messages: Annotated[List[Dict], "Messages between agents"]

# Utility functions
def log_message(agent_name: str, message: str, level: str = "INFO"):
    """Log a message with agent name and timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level} - {agent_name}: {message}")

def create_message(agent_name: str, content: str, message_type: str = "status") -> Dict[str, Any]:
    """Create a standardized message format"""
    return {
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "type": message_type,
        "content": content
    }

# Agent Functions

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

@traceable(name="analysis_agent")
def analysis_agent(state: WorkflowState) -> WorkflowState:
    """Analysis Agent - Analyzes and classifies documents using LLM"""
    agent_name = "Analysis Agent"
    log_message(agent_name, "🔍 Starting document analysis...")
    
    try:
        # Update state
        state["current_stage"] = "document_analysis"
        state["messages"].append(
            create_message(agent_name, "Starting document classification and analysis")
        )
        
        # Check if we have processed files to analyze
        processing_result = state.get("processing_result", {})
        if not processing_result or "pdf_processing" not in processing_result:
            raise Exception("No processed documents available for analysis")
        
        log_message(agent_name, "Running LLM-based document analysis...")
        
        # Execute analysis
        analysis_result = run_analysis()
        
        # Update state with results
        state["analysis_result"] = analysis_result
        
        if analysis_result and "documents" in analysis_result:
            analyzed_count = len(analysis_result["documents"])
            successful_count = len([doc for doc in analysis_result["documents"] if "error" not in doc])
            state["messages"].append(
                create_message(
                    agent_name,
                    f"Successfully analyzed {successful_count}/{analyzed_count} documents",
                    "success"
                )
            )
        else:
            state["messages"].append(
                create_message(agent_name, "Document analysis completed", "success")
            )
        
        log_message(agent_name, "✅ Document analysis completed successfully")
        return state
        
    except Exception as e:
        error_msg = f"Document analysis failed: {str(e)}"
        log_message(agent_name, error_msg, "ERROR")
        state["errors"].append(error_msg)
        state["messages"].append(create_message(agent_name, error_msg, "error"))
        return state

# Workflow functions

@traceable(name="check_scraping_success")
def check_scraping_success(state: WorkflowState) -> str:
    """Check if scraping was successful"""
    scraping_result = state.get("scraping_result", {})
    if scraping_result.get("total_downloaded_files", 0) > 0:
        return "continue"
    return "end"

@traceable(name="check_processing_success")
def check_processing_success(state: WorkflowState) -> str:
    """Check if processing was successful"""
    processing_result = state.get("processing_result")
    if processing_result and "pdf_processing" in processing_result:
        processed_count = processing_result["pdf_processing"].get("processed_files_count", 0)
        if processed_count > 0:
            return "continue"
    return "end"

@traceable(name="finalize_workflow")
def finalize_workflow(state: WorkflowState) -> WorkflowState:
    """Finalize workflow - summarize results"""
    print("\n" + "="*80)
    print("🎉 SEBI DOCUMENT PROCESSING WORKFLOW COMPLETED")
    print("="*80)
    
    # Calculate workflow duration
    start_time = datetime.fromisoformat(state["start_time"])
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Generate final report
    final_report = {
        "workflow_id": state["workflow_id"],
        "total_duration": str(duration),
        "stages_completed": state["current_stage"],
        "errors_encountered": len(state["errors"]),
        "final_status": "SUCCESS" if not state["errors"] else "COMPLETED_WITH_ERRORS"
    }
    
    # Add stage-specific results
    if "scraping_result" in state:
        scraping = state["scraping_result"]
        final_report["scraping_summary"] = {
            "pages_processed": scraping.get("pages_processed", 0),
            "files_downloaded": scraping.get("total_downloaded_files", 0),
            "links_found": scraping.get("total_links", 0)
        }
    
    if "processing_result" in state:
        processing = state["processing_result"]
        if "pdf_processing" in processing:
            pdf_proc = processing["pdf_processing"]
            final_report["processing_summary"] = {
                "files_processed": pdf_proc.get("processed_files_count", 0),
                "total_files": pdf_proc.get("total_pdf_files", 0)
            }
    
    if "analysis_result" in state:
        analysis = state["analysis_result"]
        if "documents" in analysis:
            docs = analysis["documents"]
            successful_analyses = [doc for doc in docs if "error" not in doc]
            final_report["analysis_summary"] = {
                "documents_analyzed": len(docs),
                "successful_analyses": len(successful_analyses),
                "failed_analyses": len(docs) - len(successful_analyses)
            }
    
    # Print final report
    print_final_report(final_report)
    
    # Add final message to state
    state["messages"].append({
        "agent": "Workflow Orchestrator",
        "timestamp": datetime.now().isoformat(),
        "type": "completion",
        "content": "Workflow completed successfully",
        "final_report": final_report
    })
    
    return state

def print_final_report(report: Dict[str, Any]):
    """Print a formatted final report"""
    print(f"📊 Workflow ID: {report['workflow_id']}")
    print(f"⏱️  Duration: {report['total_duration']}")
    print(f"📈 Status: {report['final_status']}")
    
    if "scraping_summary" in report:
        scraping = report["scraping_summary"]
        print(f"\n🌐 Scraping Results:")
        print(f"   📄 Pages processed: {scraping['pages_processed']}")
        print(f"   📥 Files downloaded: {scraping['files_downloaded']}")
        print(f"   🔗 Links found: {scraping['links_found']}")
    
    if "processing_summary" in report:
        processing = report["processing_summary"]
        print(f"\n📄 Processing Results:")
        print(f"   ✅ Files processed: {processing['files_processed']}")
        print(f"   📊 Total files: {processing['total_files']}")
    
    if "analysis_summary" in report:
        analysis = report["analysis_summary"]
        print(f"\n🔍 Analysis Results:")
        print(f"   📋 Documents analyzed: {analysis['documents_analyzed']}")
        print(f"   ✅ Successful: {analysis['successful_analyses']}")
        print(f"   ❌ Failed: {analysis['failed_analyses']}")
    
    if report["errors_encountered"] > 0:
        print(f"\n⚠️  Errors encountered: {report['errors_encountered']}")
    
    print("\n📁 Output Files:")
    print("   📄 scraping_metadata.json - Raw scraping data")
    print("   🔍 sebi_document_analysis_results.json - Analysis results")

def create_workflow() -> StateGraph:
    """Create the LangGraph workflow"""
    
    # Define the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes (agents) to the graph
    workflow.add_node("web_scraping", web_scraping_agent)
    workflow.add_node("document_processing", document_processing_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("finalize", finalize_workflow)
    
    # Define the workflow edges (sequence)
    workflow.add_edge(START, "web_scraping")
    workflow.add_conditional_edges(
        "web_scraping",
        check_scraping_success,
        {
            "continue": "document_processing",
            "end": "finalize"
        }
    )
    workflow.add_conditional_edges(
        "document_processing",
        check_processing_success,
        {
            "continue": "analysis",
            "end": "finalize"
        }
    )
    workflow.add_edge("analysis", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow

# Convenience functions to run the workflow
@traceable(name="run_sebi_workflow", metadata={"workflow_type": "sebi_document_processing"})
def run_sebi_workflow(
    page_numbers: List[int] = [1], 
    download_folder: str = "test_enhanced_metadata"
) -> Dict[str, Any]:
    """
    Convenience function to run the SEBI workflow
    
    Args:
        page_numbers: List of page numbers to scrape from SEBI website
        download_folder: Folder name to store downloaded PDFs
    
    Returns:
        Complete workflow results
    """
    print("🚀 Starting SEBI Document Processing Workflow")
    print("="*60)
    
    # Initialize workflow state
    workflow_id = f"sebi_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    initial_state: WorkflowState = {
        "page_numbers": page_numbers,
        "download_folder": download_folder,
        "scraping_result": {},
        "processing_result": {},
        "analysis_result": {},
        "current_stage": "initialized",
        "workflow_id": workflow_id,
        "start_time": datetime.now().isoformat(),
        "errors": [],
        "messages": []
    }
    
    # Create workflow
    workflow = create_workflow()
    
    # Create runnable workflow
    app = workflow.compile(checkpointer=MemorySaver())
    
    # Run the workflow
    config = {"configurable": {"thread_id": workflow_id}}
    final_state = app.invoke(initial_state, config)
    
    return final_state

@traceable(name="run_custom_sebi_workflow", metadata={"workflow_type": "custom_sebi_processing"})
def run_custom_sebi_workflow(
    pages: List[int],
    folder: str ='test_enhanced_metadata',
    save_results: bool = True
) -> Dict[str, Any]:
    """
    Run a custom SEBI workflow with specified parameters
    
    Args:
        pages: Page numbers to scrape
        folder: Download folder name
        save_results: Whether to save results to JSON file
    
    Returns:
        Workflow results
    """
    result = run_sebi_workflow(pages, folder)
    
    if save_results:
        # Save workflow results to JSON file
        results_file = f"workflow_results_{result['workflow_id']}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Workflow results saved to: {results_file}")
    
    return result




