"""
Database Loading Agent for SEBI Document Analysis
Handles loading analyzed document data into the PostgreSQL database
"""

import json
import asyncio
from typing import Dict, List, Any, TypedDict, Optional
from datetime import datetime
from langsmith import traceable

# Import the WorkflowState and utility functions from the shared types module
from workflow_types import WorkflowState, log_message, create_message

# Import database managers
from tool.database.index import db_manager, initialize_database
from tool.database.sebi_analysis_schema import sebi_db_manager


@traceable(name="database_loading_agent")
def database_loading_agent(state: WorkflowState) -> WorkflowState:
    """Database Loading Agent - Loads analyzed SEBI document data into PostgreSQL database"""
    agent_name = "Database Loading Agent"
    log_message(agent_name, "💾 Starting database loading process...")
    
    try:
        # Update state
        state["current_stage"] = "database_loading"
        state["messages"].append(
            create_message(agent_name, "Starting database loading process")
        )
        
        # Check if we have analysis results to load
        analysis_result = state.get("analysis_result", {})
        if not analysis_result:
            raise Exception("No analysis results available for database loading")
        
        log_message(agent_name, "Initializing database connection...")
        
        # Run the async database operations
        asyncio.run(_load_data_to_database(agent_name, state, analysis_result))
        
        log_message(agent_name, "✅ Database loading completed successfully")
        state["messages"].append(
            create_message(
                agent_name,
                "Successfully loaded all analyzed data to database",
                "success"
            )
        )
        
    except Exception as e:
        error_msg = f"Database loading failed: {str(e)}"
        log_message(agent_name, f"❌ {error_msg}")
        state["errors"].append(error_msg)
        state["messages"].append(
            create_message(agent_name, error_msg, "error")
        )
    
    return state


async def _load_data_to_database(agent_name: str, state: WorkflowState, analysis_result: Dict[str, Any]) -> None:
    """Async function to handle database loading operations"""
    
    try:
        # Initialize database tables if they don't exist
        log_message(agent_name, "Ensuring database tables exist...")
        await db_manager.create_tables()
        await sebi_db_manager.create_sebi_analysis_tables()
        
        # Load SEBI analysis data
        log_message(agent_name, "Loading SEBI analysis data...")
        metadata_id = await sebi_db_manager.insert_sebi_analysis_data(analysis_result)
        
        # Update state with database information
        state["database_result"] = {
            "metadata_id": metadata_id,
            "loaded_at": datetime.now().isoformat(),
            "total_documents": len(analysis_result.get("documents", [])),
            "success": True
        }
        
        # Also load documents into the main documents table for workflow tracking
        workflow_id = state.get("workflow_id")
        if workflow_id:
            log_message(agent_name, "Loading documents for workflow tracking...")
            await _load_workflow_documents(agent_name, state, analysis_result, workflow_id)
        
        log_message(agent_name, f"Successfully loaded data with metadata ID: {metadata_id}")
        
    except Exception as e:
        log_message(agent_name, f"Database loading error: {str(e)}")
        state["database_result"] = {
            "success": False,
            "error": str(e),
            "loaded_at": datetime.now().isoformat()
        }
        raise


async def _load_workflow_documents(agent_name: str, state: WorkflowState, 
                                 analysis_result: Dict[str, Any], workflow_id: str) -> None:
    """Load documents into the main workflow tracking tables"""
    
    try:
        documents = analysis_result.get("documents", [])
        loaded_docs = []
        
        for doc_data in documents:
            # Create document record for workflow tracking
            document_data = {
                "filename": doc_data.get("filename", ""),
                "title": doc_data.get("summary", "")[:500] if doc_data.get("summary") else None,
                "summary": doc_data.get("summary", ""),
                "department": doc_data.get("department", ""),
                "content_length": doc_data.get("content_length", 0),
                "workflow_id": workflow_id,
                "analysis_timestamp": datetime.now()
            }
            
            document_id = await db_manager.create_document(document_data)
            loaded_docs.append({
                "document_id": document_id,
                "filename": doc_data.get("filename", ""),
                "department": doc_data.get("department", "")
            })
            
            # Create actionable items in the main table for team assignments
            for item in doc_data.get("actionable_items", []):
                actionable_data = {
                    "document_id": document_id,
                    "title": item.get("action_title", ""),
                    "description": item.get("action_description", ""),
                    "responsible_parties": item.get("responsible_parties", ""),
                    "implementation_timeline": item.get("implementation_timeline", ""),
                    "compliance_requirements": item.get("compliance_requirements", ""),
                    "documentation_needed": item.get("documentation_needed", ""),
                    "monitoring_mechanism": item.get("monitoring_mechanism", ""),
                    "non_compliance_consequences": item.get("non_compliance_consequences", ""),
                    "priority": _map_priority_from_timeline(item.get("implementation_timeline", "")),
                    "is_completed": False
                }
                
                await db_manager.create_actionable_item(actionable_data)
        
        # Update state with workflow document information
        state["workflow_documents"] = loaded_docs
        log_message(agent_name, f"Loaded {len(loaded_docs)} documents for workflow tracking")
        
    except Exception as e:
        log_message(agent_name, f"Error loading workflow documents: {str(e)}")
        raise


def _map_priority_from_timeline(timeline: str) -> str:
    """Map implementation timeline to priority level"""
    if not timeline:
        return "medium"
    
    timeline_lower = timeline.lower()
    
    if "immediate" in timeline_lower or "urgent" in timeline_lower:
        return "critical"
    elif "30 days" in timeline_lower or "1 month" in timeline_lower:
        return "high"
    elif "60 days" in timeline_lower or "2 month" in timeline_lower:
        return "medium"
    else:
        return "low"


@traceable(name="create_ai_team_assignments")
def create_ai_team_assignments(state: WorkflowState) -> WorkflowState:
    """Create AI-suggested team assignments for documents based on department and content"""
    agent_name = "Database Loading Agent"
    
    try:
        workflow_documents = state.get("workflow_documents", [])
        if not workflow_documents:
            log_message(agent_name, "No workflow documents available for team assignment")
            return state
        
        log_message(agent_name, "Creating AI-suggested team assignments...")
        
        # Run async assignment creation
        asyncio.run(_create_assignments(agent_name, state, workflow_documents))
        
        log_message(agent_name, "✅ AI team assignments created successfully")
        
    except Exception as e:
        error_msg = f"Team assignment creation failed: {str(e)}"
        log_message(agent_name, f"❌ {error_msg}")
        state["errors"].append(error_msg)
    
    return state


async def _create_assignments(agent_name: str, state: WorkflowState, workflow_documents: List[Dict[str, Any]]) -> None:
    """Create team assignments based on document department and content"""
    
    try:
        # Get all teams
        teams = await db_manager.get_all_teams()
        if not teams:
            # Initialize default teams if none exist
            await initialize_database()
            teams = await db_manager.get_all_teams()
        
        team_map = {team["type"]: team["id"] for team in teams}
        assignments_created = []
        
        for doc in workflow_documents:
            department = doc.get("department", "").lower()
            document_id = doc["document_id"]
            
            # AI logic for team assignment based on department
            suggested_teams = _suggest_teams_for_department(department)
            
            for team_type, reason in suggested_teams:
                if team_type in team_map:
                    assignment_data = {
                        "document_id": document_id,
                        "team_id": team_map[team_type],
                        "status": "ai_suggested",
                        "priority": "medium",
                        "assigned_by": "AI System",
                        "ai_suggestion_reason": reason
                    }
                    
                    assignment_id = await db_manager.create_document_assignment(assignment_data)
                    assignments_created.append({
                        "assignment_id": assignment_id,
                        "document_id": document_id,
                        "team_type": team_type,
                        "reason": reason
                    })
        
        state["ai_assignments"] = assignments_created
        log_message(agent_name, f"Created {len(assignments_created)} AI-suggested assignments")
        
    except Exception as e:
        log_message(agent_name, f"Error creating assignments: {str(e)}")
        raise


def _suggest_teams_for_department(department: str) -> List[tuple[str, str]]:
    """Suggest appropriate teams based on document department"""
    suggestions = []
    
    if "legal" in department or "compliance" in department or "regulation" in department:
        suggestions.append(("legal_compliance", "Legal and regulatory content requires compliance expertise"))
    
    if "risk" in department or "management" in department:
        suggestions.append(("risk_management", "Risk management implications identified"))
    
    if "investment" in department or "mutual fund" in department or "portfolio" in department:
        suggestions.append(("finance", "Financial services and investment content"))
    
    if "market" in department or "intermediary" in department or "supervision" in department:
        suggestions.append(("operations", "Market operations and intermediary supervision"))
    
    if "executive" in department or "policy" in department or "strategic" in department:
        suggestions.append(("executive", "Strategic policy decisions required"))
    
    # Default assignment if no specific match
    if not suggestions:
        suggestions.append(("legal_compliance", "Default assignment for regulatory document"))
    
    return suggestions


# Additional utility functions for database operations

@traceable(name="load_json_file_to_database")
async def load_json_file_to_database(file_path: str) -> Dict[str, Any]:
    """Load SEBI analysis data from JSON file directly to database"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # Initialize database
        await db_manager.create_tables()
        await sebi_db_manager.create_sebi_analysis_tables()
        
        # Load data
        metadata_id = await sebi_db_manager.insert_sebi_analysis_data(analysis_data)
        
        return {
            "success": True,
            "metadata_id": metadata_id,
            "total_documents": len(analysis_data.get("documents", [])),
            "loaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "loaded_at": datetime.now().isoformat()
        }


@traceable(name="get_database_summary")
async def get_database_summary() -> Dict[str, Any]:
    """Get comprehensive database summary"""
    try:
        # Get health check
        health = await db_manager.health_check()
        
        # Get SEBI compliance summary
        compliance_summary = await sebi_db_manager.get_compliance_summary()
        
        # Get team workload
        team_workload = await db_manager.get_team_workload_summary()
        
        return {
            "database_health": health,
            "compliance_summary": compliance_summary,
            "team_workload": team_workload,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }


# Export functions
__all__ = [
    'database_loading_agent',
    'create_ai_team_assignments', 
    'load_json_file_to_database',
    'get_database_summary'
]
