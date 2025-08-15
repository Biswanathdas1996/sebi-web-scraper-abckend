# Import necessary modules and dependencies
from typing import Dict, List, Any, TypedDict
from datetime import datetime
from langsmith import traceable

# Import the WorkflowState and utility functions from the shared types module
from workflow_types import WorkflowState, log_message, create_message

# Import the analysis functionality
from tool.classiflire.index import run_analysis


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
