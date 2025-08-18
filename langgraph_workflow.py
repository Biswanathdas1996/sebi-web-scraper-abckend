import json
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime
# Load environment variables
from dotenv import load_dotenv

# LangSmith tracing setup
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from langsmith_config import configure_langsmith, validate_langsmith_setup

# Import shared workflow types and utilities
from workflow_types import WorkflowState, log_message, create_message

from agents.web_scraping_agent import web_scraping_agent
from agents.document_processing_agent import document_processing_agent
from agents.analysis_agent import analysis_agent
from agents.database_loading_agent import database_loading_agent, create_ai_team_assignments

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

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


# conditional routing functions

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

@traceable(name="check_analysis_success")
def check_analysis_success(state: WorkflowState) -> str:
    """Check if analysis was successful"""
    analysis_result = state.get("analysis_result", {})
    if analysis_result and "documents" in analysis_result:
        documents = analysis_result["documents"]
        successful_analyses = [doc for doc in documents if "error" not in doc]
        if len(successful_analyses) > 0:
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
    
    # Add database loading results
    if "database_result" in state:
        db_result = state["database_result"]
        final_report["database_summary"] = {
            "success": db_result.get("success", False),
            "metadata_id": db_result.get("metadata_id", ""),
            "total_documents_loaded": db_result.get("total_documents", 0),
            "loaded_at": db_result.get("loaded_at", "")
        }
    
    # Add team assignment results
    if "ai_assignments" in state:
        assignments = state["ai_assignments"]
        final_report["team_assignments_summary"] = {
            "total_assignments_created": len(assignments),
            "assigned_teams": len(set(a.get("team_type", "") for a in assignments))
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
    
    if "database_summary" in report:
        db = report["database_summary"]
        print(f"\n💾 Database Loading Results:")
        print(f"   📊 Success: {db['success']}")
        print(f"   🔑 Metadata ID: {db['metadata_id']}")
        print(f"   📄 Documents loaded: {db['total_documents_loaded']}")
    
    if "team_assignments_summary" in report:
        assignments = report["team_assignments_summary"]
        print(f"\n👥 Team Assignment Results:")
        print(f"   📋 Total assignments: {assignments['total_assignments_created']}")
        print(f"   🏢 Teams involved: {assignments['assigned_teams']}")
    
    if report["errors_encountered"] > 0:
        print(f"\n⚠️  Errors encountered: {report['errors_encountered']}")
    
    print("\n📁 Output Files:")
    print("   📄 scraping_metadata.json - Raw scraping data")
    print("   🔍 sebi_document_analysis_results.json - Analysis results")
    print("   💾 Database - Loaded into PostgreSQL with team assignments")

def create_workflow() -> StateGraph:
    """Create the LangGraph workflow"""
    
    # Define the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes (agents) to the graph
    workflow.add_node("web_scraping", web_scraping_agent)
    workflow.add_node("document_processing", document_processing_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("database_loading", database_loading_agent)
    workflow.add_node("team_assignments", create_ai_team_assignments)
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
    workflow.add_conditional_edges(
        "analysis",
        check_analysis_success,
        {
            "continue": "database_loading",
            "end": "finalize"
        }
    )
    workflow.add_edge("database_loading", "team_assignments")
    workflow.add_edge("team_assignments", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow

# Convenience functions to run the workflow
@traceable(name="run_sebi_workflow", metadata={"workflow_type": "sebi_document_processing"})
def run_sebi_workflow(
    page_numbers: List[int] = [1], 
    download_folder: str = "test_enhanced_metadata"
) -> Dict[str, Any]:
    
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
        "database_result": {},
        "workflow_documents": [],
        "ai_assignments": [],
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
    save_results: bool = False
) -> Dict[str, Any]:
   
    result = run_sebi_workflow(pages, folder)
    
    if save_results:
        # Save workflow results to JSON file
        results_file = f"workflow_results_{result['workflow_id']}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Workflow results saved to: {results_file}")
    
    return result




