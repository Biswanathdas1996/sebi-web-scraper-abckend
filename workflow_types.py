"""
Shared types and utilities for the SEBI document processing workflow.
This module contains the WorkflowState definition and utility functions
that are used across all agents to avoid circular imports.
"""

from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime


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
    database_result: Dict[str, Any]
    workflow_documents: List[Dict[str, Any]]
    ai_assignments: List[Dict[str, Any]]
    
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
