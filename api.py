from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from typing import List, Dict, Any, Optional
import os
import json
import threading
from datetime import datetime
import uuid
import asyncio
import asyncpg

# Import the LangGraph workflow
from langgraph_workflow import run_custom_sebi_workflow
from langsmith_config import get_langsmith_config

# Import database managers
from tool.database.index import db_manager, initialize_database
from tool.database.sebi_analysis_schema import sebi_db_manager

# Import chat bot functionality
from chatBot.index import chat_bot_response

# Database connection URL
DATABASE_URL = "postgresql://neondb_owner:npg_Gyfsvm73xnHF@ep-round-fog-aeqh1bw4-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains and routes

app.config['JSON_SORT_KEYS'] = False

# In-memory storage for task status (in production, use Redis or database)
task_storage: Dict[str, Dict[str, Any]] = {}

def run_workflow_task(task_id: str, page_numbers: List[int], download_folder: str, save_results: bool):
    """Background task to run the workflow"""
    try:
        task_storage[task_id]["status"] = "running"
        task_storage[task_id]["message"] = "Workflow execution started"
        
        print(f"🚀 Starting workflow task {task_id}")
        result = run_custom_sebi_workflow(page_numbers, download_folder, save_results)
        
        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["message"] = "Workflow execution completed successfully"
        task_storage[task_id]["result"] = result
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        
        print(f"✅ Workflow task {task_id} completed successfully")
        
    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["message"] = f"Workflow execution failed: {str(e)}"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        
        print(f"❌ Workflow task {task_id} failed: {str(e)}")

@app.route("/", methods=["GET"])
def root():
    """Health check endpoint"""
    langsmith_config = get_langsmith_config()
    return jsonify({
        "message": "SEBI Document Processing API is running",
        "version": "1.0.0",
        "langsmith_enabled": langsmith_config.get("tracing_enabled", False),
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "GET /",
            "api_documentation": "GET /api/docs",
            "workflow": {
                "trigger": "POST /api/trigger-workflow",
                "status": "GET /api/workflow-status/<task_id>",
                "list_tasks": "GET /api/list-tasks",
                "clear_tasks": "DELETE /api/clear-tasks"
            },
            "files": {
                "scraping_metadata": "GET /api/scraping-metadata",
                "analysis_results": "GET /api/analysis-results",
                "sebi_circular_content": "GET /api/sebi-circular?sebi_circular_ref=<ref>",
                "sebi_circular_qa": "POST /api/sebi-circular-qa",
                "download_metadata": "GET /api/download-scraping-metadata",
                "download_results": "GET /api/download-analysis-results"
            },
            "database": {
                "all_tables": "GET /api/database/tables",
                "schema": "GET /api/database/schema",
                "specific_table": "GET /api/database/table/<table_name>",
                "summary": "GET /api/database/summary"
            },
            "chatbot": {
                "chat": "POST /api/chatbot/chat"
            }
        }
    })

@app.route("/api/trigger-workflow", methods=["POST"])
def trigger_workflow():
    """
    Trigger the SEBI document processing workflow
    
    Expected JSON payload:
    {
        "page_numbers": [1, 2, 3],  # optional, default: [1]
        "download_folder": "test_enhanced_metadata",  # optional
        "save_results": true  # optional, default: true
    }
    """
    try:
        # Get request data
        data = request.get_json() or {}
        page_numbers = data.get("page_numbers", [1])
        download_folder = data.get("download_folder", "test_enhanced_metadata")
        save_results = data.get("save_results", True)
        
        # Validate input
        if not isinstance(page_numbers, list) or not all(isinstance(p, int) for p in page_numbers):
            return jsonify({"error": "page_numbers must be a list of integers"}), 400
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task storage
        task_storage[task_id] = {
            "status": "initiated",
            "message": "Workflow task initiated",
            "started_at": datetime.now().isoformat(),
            "page_numbers": page_numbers,
            "download_folder": download_folder,
            "save_results": save_results
        }
        
        # Start background task
        thread = threading.Thread(
            target=run_workflow_task,
            args=(task_id, page_numbers, download_folder, save_results)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "status": "initiated",
            "message": "Workflow has been initiated and is running in the background",
            "started_at": task_storage[task_id]["started_at"]
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to trigger workflow: {str(e)}"}), 500

@app.route("/api/workflow-status/<task_id>", methods=["GET"])
def get_workflow_status(task_id: str):
    """
    Get the status of a workflow task
    """
    if task_id not in task_storage:
        return jsonify({"error": "Task not found"}), 404
    
    task_info = task_storage[task_id]
    
    response_data = {
        "task_id": task_id,
        "status": task_info["status"],
        "workflow_id": task_info.get("result", {}).get("workflow_id", "N/A")
    }
    
    # Add additional fields based on status
    if task_info["status"] == "completed":
        result = task_info.get("result", {})
        final_message = result.get("messages", [])
        final_report = {}
        
        # Extract final report from the last message
        if final_message:
            last_message = final_message[-1]
            if isinstance(last_message, dict) and "final_report" in last_message:
                final_report = last_message["final_report"]
        
        response_data.update({
            "duration": final_report.get("total_duration"),
            "final_status": final_report.get("final_status"),
            "errors": result.get("errors", []),
            "results": {
                "scraping_summary": final_report.get("scraping_summary"),
                "processing_summary": final_report.get("processing_summary"),
                "analysis_summary": final_report.get("analysis_summary")
            }
        })
    
    elif task_info["status"] == "failed":
        response_data.update({
            "errors": [task_info.get("error", "Unknown error")],
            "final_status": "FAILED"
        })
    
    return jsonify(response_data)

@app.route("/api/scraping-metadata", methods=["GET"])
def get_scraping_metadata():
    """
    Get the scraping metadata JSON file
    """
    file_path = os.path.join("output", "scraping_metadata.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Scraping metadata file not found"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        return jsonify({
            "message": "Scraping metadata retrieved successfully",
            "file_path": file_path,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    except json.JSONDecodeError:
        return jsonify({"error": "Error reading scraping metadata file"}), 500
    except Exception as e:
        return jsonify({"error": f"Error retrieving scraping metadata: {str(e)}"}), 500

@app.route("/api/analysis-results", methods=["GET"])
def get_analysis_results():
    """
    Get the SEBI document analysis results JSON file
    """
    file_path = os.path.join("output", "sebi_document_analysis_results.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Analysis results file not found"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        return jsonify({
            "message": "Analysis results retrieved successfully",
            "file_path": file_path,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    except json.JSONDecodeError:
        return jsonify({"error": "Error reading analysis results file"}), 500
    except Exception as e:
        return jsonify({"error": f"Error retrieving analysis results: {str(e)}"}), 500

@app.route("/api/download-scraping-metadata", methods=["GET"])
def download_scraping_metadata():
    """
    Download the scraping metadata JSON file
    """
    file_path = os.path.join("output", "scraping_metadata.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Scraping metadata file not found"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name="scraping_metadata.json",
        mimetype="application/json"
    )

@app.route("/api/download-analysis-results", methods=["GET"])
def download_analysis_results():
    """
    Download the SEBI document analysis results JSON file
    """
    file_path = os.path.join("output", "sebi_document_analysis_results.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Analysis results file not found"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name="sebi_document_analysis_results.json",
        mimetype="application/json"
    )

@app.route("/api/list-tasks", methods=["GET"])
def list_tasks():
    """
    List all workflow tasks and their status
    """
    tasks_summary = []
    
    for task_id, task_info in task_storage.items():
        summary = {
            "task_id": task_id,
            "status": task_info["status"],
            "started_at": task_info["started_at"],
            "page_numbers": task_info.get("page_numbers", []),
            "download_folder": task_info.get("download_folder", "")
        }
        
        if "completed_at" in task_info:
            summary["completed_at"] = task_info["completed_at"]
        
        if task_info["status"] == "completed" and "result" in task_info:
            result = task_info["result"]
            summary["workflow_id"] = result.get("workflow_id", "N/A")
        
        tasks_summary.append(summary)
    
    return jsonify({
        "message": f"Found {len(tasks_summary)} tasks",
        "tasks": tasks_summary,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/clear-tasks", methods=["DELETE"])
def clear_tasks():
    """
    Clear all completed and failed tasks from memory
    """
    initial_count = len(task_storage)
    
    # Keep only running tasks
    running_tasks = {k: v for k, v in task_storage.items() if v["status"] == "running"}
    task_storage.clear()
    task_storage.update(running_tasks)
    
    cleared_count = initial_count - len(task_storage)
    
    return jsonify({
        "message": f"Cleared {cleared_count} completed/failed tasks",
        "remaining_tasks": len(task_storage),
        "timestamp": datetime.now().isoformat()
    })

# Database API endpoints

async def get_async_connection():
    """Get async database connection"""
    return await asyncpg.connect(DATABASE_URL)

async def get_all_tables_data():
    """Fetch all tables and their data from the database"""
    conn = await get_async_connection()
    try:
        # Define all the tables we want to fetch
        tables_info = {
            # Main workflow tables
            "teams": {
                "query": "SELECT * FROM teams ORDER BY name",
                "description": "Team management data"
            },
            "documents": {
                "query": "SELECT * FROM documents ORDER BY created_at DESC",
                "description": "Document metadata and processing information"
            },
            "document_assignments": {
                "query": """
                    SELECT da.*, t.name as team_name, t.type as team_type, 
                           d.filename, d.title as document_title
                    FROM document_assignments da
                    LEFT JOIN teams t ON da.team_id = t.id
                    LEFT JOIN documents d ON da.document_id = d.id
                    ORDER BY da.created_at DESC
                """,
                "description": "Document assignments to teams"
            },
            "actionable_items": {
                "query": """
                    SELECT ai.*, d.filename, d.title as document_title
                    FROM actionable_items ai
                    LEFT JOIN documents d ON ai.document_id = d.id
                    ORDER BY ai.created_at DESC
                """,
                "description": "Actionable items from documents"
            },
            "item_assignments": {
                "query": """
                    SELECT ia.*, ai.title as item_title, t.name as team_name, t.type as team_type
                    FROM item_assignments ia
                    LEFT JOIN actionable_items ai ON ia.actionable_item_id = ai.id
                    LEFT JOIN teams t ON ia.team_id = t.id
                    ORDER BY ia.created_at DESC
                """,
                "description": "Assignment of actionable items to teams"
            },
            "assignment_timeline": {
                "query": """
                    SELECT at.*, 
                           ft.name as from_team_name, ft.type as from_team_type,
                           tt.name as to_team_name, tt.type as to_team_type
                    FROM assignment_timeline at
                    LEFT JOIN teams ft ON at.from_team_id = ft.id
                    LEFT JOIN teams tt ON at.to_team_id = tt.id
                    ORDER BY at.created_at DESC
                """,
                "description": "Timeline of assignment changes"
            },
            
            # SEBI analysis tables
            "sebi_analysis_metadata": {
                "query": "SELECT * FROM sebi_analysis_metadata ORDER BY created_at DESC",
                "description": "SEBI analysis workflow metadata"
            },
            "sebi_documents": {
                "query": """
                    SELECT sd.*, sam.workflow_id, sam.analysis_timestamp as metadata_analysis_timestamp
                    FROM sebi_documents sd
                    LEFT JOIN sebi_analysis_metadata sam ON sd.analysis_metadata_id = sam.id
                    ORDER BY sd.circular_date DESC NULLS LAST, sd.created_at DESC
                """,
                "description": "SEBI documents with analysis results"
            },
            "sebi_key_clauses": {
                "query": """
                    SELECT skc.*, sd.filename, sd.department
                    FROM sebi_key_clauses skc
                    LEFT JOIN sebi_documents sd ON skc.document_id = sd.id
                    ORDER BY skc.effective_date DESC NULLS LAST, skc.created_at DESC
                """,
                "description": "Key regulatory clauses from SEBI documents"
            },
            "sebi_key_metrics": {
                "query": """
                    SELECT skm.*, sd.filename, sd.department
                    FROM sebi_key_metrics skm
                    LEFT JOIN sebi_documents sd ON skm.document_id = sd.id
                    ORDER BY skm.created_at DESC
                """,
                "description": "Key metrics and measurements from SEBI documents"
            },
            "sebi_actionable_items": {
                "query": """
                    SELECT sai.*, sd.filename, sd.department
                    FROM sebi_actionable_items sai
                    LEFT JOIN sebi_documents sd ON sai.document_id = sd.id
                    ORDER BY sai.is_completed ASC, sai.created_at DESC
                """,
                "description": "Actionable items identified in SEBI documents"
            }
        }
        
        result = {}
        total_records = 0
        
        for table_name, table_info in tables_info.items():
            try:
                # Check if table exists
                table_exists = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                """, table_name)
                
                if table_exists:
                    rows = await conn.fetch(table_info["query"])
                    data = [dict(row) for row in rows]
                    
                    result[table_name] = {
                        "description": table_info["description"],
                        "record_count": len(data),
                        "data": data
                    }
                    total_records += len(data)
                else:
                    result[table_name] = {
                        "description": table_info["description"],
                        "record_count": 0,
                        "data": [],
                        "status": "table_not_exists"
                    }
                    
            except Exception as e:
                result[table_name] = {
                    "description": table_info["description"],
                    "record_count": 0,
                    "data": [],
                    "error": str(e),
                    "status": "query_failed"
                }
        
        return {
            "status": "success",
            "total_tables": len(tables_info),
            "total_records": total_records,
            "tables": result,
            "generated_at": datetime.now().isoformat()
        }
        
    finally:
        await conn.close()

async def get_table_schema():
    """Get schema information for all tables"""
    conn = await get_async_connection()
    try:
        schema_query = """
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            AND t.table_name IN (
                'teams', 'documents', 'document_assignments', 'actionable_items', 
                'item_assignments', 'assignment_timeline', 'sebi_analysis_metadata',
                'sebi_documents', 'sebi_key_clauses', 'sebi_key_metrics', 'sebi_actionable_items'
            )
            ORDER BY t.table_name, c.ordinal_position
        """
        
        rows = await conn.fetch(schema_query)
        
        # Group columns by table
        schema_info = {}
        for row in rows:
            table_name = row['table_name']
            if table_name not in schema_info:
                schema_info[table_name] = {
                    "columns": [],
                    "column_count": 0
                }
            
            column_info = {
                "name": row['column_name'],
                "type": row['data_type'],
                "nullable": row['is_nullable'] == 'YES',
                "default": row['column_default'],
                "max_length": row['character_maximum_length'],
                "precision": row['numeric_precision'],
                "scale": row['numeric_scale']
            }
            
            schema_info[table_name]["columns"].append(column_info)
            schema_info[table_name]["column_count"] += 1
        
        return {
            "status": "success",
            "tables": schema_info,
            "total_tables": len(schema_info),
            "generated_at": datetime.now().isoformat()
        }
        
    finally:
        await conn.close()

@app.route("/api/database/tables", methods=["GET"])
def get_all_database_tables():
    """
    Get all tables in the database with their data
    """
    try:
        # Run async function in current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_all_tables_data())
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch database tables: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/database/schema", methods=["GET"])
def get_database_schema():
    """
    Get schema information for all database tables
    """
    try:
        # Run async function in current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_table_schema())
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch database schema: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/database/table/<table_name>", methods=["GET"])
def get_specific_table_data(table_name: str):
    """
    Get data from a specific table
    """
    try:
        # Validate table name to prevent SQL injection
        allowed_tables = [
            'teams', 'documents', 'document_assignments', 'actionable_items', 
            'item_assignments', 'assignment_timeline', 'sebi_analysis_metadata',
            'sebi_documents', 'sebi_key_clauses', 'sebi_key_metrics', 'sebi_actionable_items'
        ]
        
        if table_name not in allowed_tables:
            return jsonify({
                "status": "error",
                "message": f"Table '{table_name}' is not allowed or does not exist",
                "allowed_tables": allowed_tables
            }), 400
        
        async def get_table_data():
            conn = await get_async_connection()
            try:
                # Get query parameters
                limit = request.args.get('limit', 100, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                total_count = await conn.fetchval(count_query)
                
                # Get data with pagination
                data_query = f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT $1 OFFSET $2"
                rows = await conn.fetch(data_query, limit, offset)
                data = [dict(row) for row in rows]
                
                return {
                    "status": "success",
                    "table_name": table_name,
                    "total_records": total_count,
                    "returned_records": len(data),
                    "limit": limit,
                    "offset": offset,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                await conn.close()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_table_data())
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch table data: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/database/summary", methods=["GET"])
def get_database_summary():
    """
    Get a summary of database status and statistics
    """
    try:
        async def get_db_summary():
            conn = await get_async_connection()
            try:
                # Get table counts
                tables = [
                    'teams', 'documents', 'document_assignments', 'actionable_items', 
                    'item_assignments', 'assignment_timeline', 'sebi_analysis_metadata',
                    'sebi_documents', 'sebi_key_clauses', 'sebi_key_metrics', 'sebi_actionable_items'
                ]
                
                table_counts = {}
                total_records = 0
                
                for table in tables:
                    try:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        table_counts[table] = count
                        total_records += count
                    except:
                        table_counts[table] = 0
                
                # Get recent activity (last 7 days)
                recent_activity = {}
                for table in ['documents', 'sebi_documents', 'document_assignments']:
                    try:
                        if table == 'documents':
                            recent_count = await conn.fetchval("""
                                SELECT COUNT(*) FROM documents 
                                WHERE created_at >= NOW() - INTERVAL '7 days'
                            """)
                        elif table == 'sebi_documents':
                            recent_count = await conn.fetchval("""
                                SELECT COUNT(*) FROM sebi_documents 
                                WHERE created_at >= NOW() - INTERVAL '7 days'
                            """)
                        else:
                            recent_count = await conn.fetchval("""
                                SELECT COUNT(*) FROM document_assignments 
                                WHERE created_at >= NOW() - INTERVAL '7 days'
                            """)
                        recent_activity[table] = recent_count
                    except:
                        recent_activity[table] = 0
                
                # Get completion status
                completion_stats = {}
                try:
                    # Document assignments by status
                    assignment_stats = await conn.fetch("""
                        SELECT status, COUNT(*) as count 
                        FROM document_assignments 
                        GROUP BY status
                    """)
                    completion_stats['assignment_status'] = {row['status']: row['count'] for row in assignment_stats}
                    
                    # Actionable items completion
                    actionable_completion = await conn.fetchrow("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN is_completed THEN 1 END) as completed
                        FROM sebi_actionable_items
                    """)
                    if actionable_completion:
                        total = actionable_completion['total']
                        completed = actionable_completion['completed']
                        completion_stats['actionable_items'] = {
                            'total': total,
                            'completed': completed,
                            'pending': total - completed,
                            'completion_rate': (completed / total * 100) if total > 0 else 0
                        }
                except:
                    pass
                
                return {
                    "status": "success",
                    "database_health": "healthy",
                    "table_counts": table_counts,
                    "total_records": total_records,
                    "recent_activity_7_days": recent_activity,
                    "completion_statistics": completion_stats,
                    "generated_at": datetime.now().isoformat()
                }
                
            finally:
                await conn.close()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_db_summary())
            return jsonify(result)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get database summary: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# Chatbot API endpoint

@app.route("/api/chatbot/chat", methods=["POST"])
def chat_with_bot():
    """
    Chat with the SEBI regulatory compliance bot
    
    Expected JSON payload:
    {
        "query": "For stock broker released for last 1 month",  # required
        "time_range": "last 1 month"  # optional, default: "last 1 month"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        query = data.get("query")
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        # Run the chat bot response in async context
        async def get_chat_response():
            return await chat_bot_response(query)
        
        # Execute async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(get_chat_response())
            
            # Add request information to response
            response["request_info"] = {
                "query": query,
                
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "error": f"Chat bot request failed: {str(e)}",
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/sebi-circular", methods=["GET"])
def get_sebi_circular_content():
    """
    Get extracted content for a specific SEBI circular reference
    
    Query Parameters:
    - sebi_circular_ref: The SEBI circular reference identifier (e.g., SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118)
    """
    try:
        # Get sebi_circular_ref from query parameters
        sebi_circular_ref = request.args.get('sebi_circular_ref')
        
        if not sebi_circular_ref:
            return jsonify({
                "error": "sebi_circular_ref query parameter is required",
                "status": "missing_parameter",
                "example": "/api/sebi-circular?sebi_circular_ref=SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118"
            }), 400
        # Read the scraping metadata file
        metadata_file_path = os.path.join("output", "scraping_metadata.json")
        
        if not os.path.exists(metadata_file_path):
            return jsonify({
                "error": "Scraping metadata file not found",
                "status": "file_not_found"
            }), 404
        
        # Load the metadata
        with open(metadata_file_path, 'r', encoding='utf-8') as file:
            metadata = json.load(file)
        
        # Search for the circular reference in all page results and files
        found_file = None
        for page_result in metadata.get("page_results", []):
            for file_info in page_result.get("files", []):
                if file_info.get("sebi_circular_ref") == sebi_circular_ref:
                    found_file = file_info
                    break
            if found_file:
                break
        
        if not found_file:
            return jsonify({
                "error": f"SEBI circular with reference '{sebi_circular_ref}' not found",
                "status": "not_found",
                "available_references": [
                    file_info.get("sebi_circular_ref") 
                    for page_result in metadata.get("page_results", [])
                    for file_info in page_result.get("files", [])
                    if file_info.get("sebi_circular_ref")
                ]
            }), 404
        
        # Extract the content
        extracted_content = found_file.get("extracted_content")
        
        if not extracted_content:
            return jsonify({
                "error": f"No extracted content found for SEBI circular '{sebi_circular_ref}'",
                "status": "no_content"
            }), 404
        
        # Return the extracted content with metadata
        response_data = {
            "status": "success",
            "sebi_circular_ref": sebi_circular_ref,
            "circular_date": found_file.get("circular_date"),
            "circular_number": found_file.get("circular_number"),
            "document_title": found_file.get("text", ""),
            "source_url": found_file.get("source_url"),
            "file_info": {
                "filename": found_file.get("original_filename"),
                "file_size": found_file.get("file_size"),
                "file_path": found_file.get("file_path")
            },
            "extracted_content": extracted_content,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except json.JSONDecodeError:
        return jsonify({
            "error": "Error reading scraping metadata file - invalid JSON format",
            "status": "json_error"
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Error retrieving SEBI circular content: {str(e)}",
            "status": "server_error"
        }), 500

@app.route("/api/sebi-circular-qa", methods=["POST"])
def sebi_circular_qa():
    """
    Q&A on a single SEBI circular using extracted content and LLM
    
    Expected JSON payload:
    {
        "sebi_circular_ref": "SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118",  # required
        "query": "What are the key compliance requirements?"  # required
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        sebi_circular_ref = data.get("sebi_circular_ref")
        query = data.get("query")
        
        if not sebi_circular_ref:
            return jsonify({
                "error": "sebi_circular_ref parameter is required",
                "status": "missing_parameter"
            }), 400
        
        if not query:
            return jsonify({
                "error": "query parameter is required", 
                "status": "missing_parameter"
            }), 400
        
        # Read the scraping metadata file
        metadata_file_path = os.path.join("output", "scraping_metadata.json")
        
        if not os.path.exists(metadata_file_path):
            return jsonify({
                "error": "Scraping metadata file not found",
                "status": "file_not_found"
            }), 404
        
        # Load the metadata
        with open(metadata_file_path, 'r', encoding='utf-8') as file:
            metadata = json.load(file)
        
        # Search for the circular reference in all page results and files
        found_file = None
        for page_result in metadata.get("page_results", []):
            for file_info in page_result.get("files", []):
                if file_info.get("sebi_circular_ref") == sebi_circular_ref:
                    found_file = file_info
                    break
            if found_file:
                break
        
        if not found_file:
            return jsonify({
                "error": f"SEBI circular with reference '{sebi_circular_ref}' not found",
                "status": "not_found",
                "available_references": [
                    file_info.get("sebi_circular_ref") 
                    for page_result in metadata.get("page_results", [])
                    for file_info in page_result.get("files", [])
                    if file_info.get("sebi_circular_ref")
                ]
            }), 404
        
        # Extract the content
        extracted_content = found_file.get("extracted_content")
        
        if not extracted_content:
            return jsonify({
                "error": f"No extracted content found for SEBI circular '{sebi_circular_ref}'",
                "status": "no_content"
            }), 404
        
        # Create context for LLM
        context = {
            "sebi_circular_ref": sebi_circular_ref,
            "circular_date": found_file.get("circular_date"),
            "circular_number": found_file.get("circular_number"),
            "document_title": found_file.get("text", ""),
            "source_url": found_file.get("source_url"),
            "extracted_content": extracted_content
        }
        
        # Create prompt for LLM
        def create_sebi_circular_qa_prompt(context_data, user_query):
            context_json = json.dumps(context_data, indent=2)
            
            prompt = f"""You are a SEBI regulatory compliance expert. Answer the user's question based on the provided SEBI circular content.

SEBI CIRCULAR CONTEXT:
{context_json}

USER QUESTION: {user_query}

INSTRUCTIONS:
- Provide a comprehensive and accurate answer based ONLY on the content provided
- If the specific information is not available in the document, clearly state "Information not available in this circular"
- Include relevant quotes or references from the document when applicable
- Structure your response clearly with headings and bullet points where appropriate
- If the query asks about compliance requirements, timelines, or specific procedures, be precise and detailed
- Include any relevant dates, deadlines, or effective dates mentioned in the circular

RESPONSE FORMAT:
## Answer

[Your precise answer here]

## Key Points
- [Important points from the circular]
- [Relevant compliance requirements]
- [Timeline or deadlines if applicable]

## Document References
- SEBI Circular Reference: {context_data.get('sebi_circular_ref', 'N/A')}
- Circular Date: {context_data.get('circular_date', 'N/A')}
- Document Title: {context_data.get('document_title', 'N/A')}

Note: This response is based solely on the content of the specified SEBI circular. For complete regulatory guidance, please refer to the full circular and consult with compliance experts.
"""
            return prompt
        
        # Run the LLM analysis in async context
        async def get_qa_response():
            prompt = create_sebi_circular_qa_prompt(context, query)
            
            # Import the LLM function
            from tool.LLM.index import call_pwc_genai
            
            llm_response = await call_pwc_genai(
                model="vertex_ai.gemini-2.0-flash", 
                prompt=prompt
            )
            
            # Extract the result
            result = llm_response.get('choices', [{}])[0].get('text', '')
            
            return result
        
        # Execute async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            llm_answer = loop.run_until_complete(get_qa_response())
            
            response_data = {
                "status": "success",
                "sebi_circular_ref": sebi_circular_ref,
                "query": query,
                "answer": llm_answer,
                "document_metadata": {
                    "circular_date": found_file.get("circular_date"),
                    "circular_number": found_file.get("circular_number"),
                    "document_title": found_file.get("text", ""),
                    "source_url": found_file.get("source_url"),
                    "filename": found_file.get("original_filename")
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response_data)
            
        finally:
            loop.close()
        
    except json.JSONDecodeError:
        return jsonify({
            "error": "Error reading scraping metadata file - invalid JSON format",
            "status": "json_error"
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Error processing SEBI circular Q&A: {str(e)}",
            "status": "server_error"
        }), 500

@app.route("/api/docs", methods=["GET"])
def get_api_documentation():
    """
    Get comprehensive API documentation
    """
    docs = {
        "api_title": "SEBI Document Processing API",
        "version": "1.0.0",
        "description": "API for processing SEBI documents and managing database operations",
        "base_url": "http://localhost:8000",
        "generated_at": datetime.now().isoformat(),
        
        "workflow_endpoints": {
            "POST /api/trigger-workflow": {
                "description": "Trigger the SEBI document processing workflow",
                "parameters": {
                    "page_numbers": "List of integers (optional, default: [1])",
                    "download_folder": "String (optional, default: 'test_enhanced_metadata')",
                    "save_results": "Boolean (optional, default: true)"
                },
                "response": "Task ID and status information"
            },
            "GET /api/workflow-status/<task_id>": {
                "description": "Get the status of a workflow task",
                "parameters": {
                    "task_id": "String (required) - UUID of the task"
                },
                "response": "Task status, progress, and results"
            },
            "GET /api/list-tasks": {
                "description": "List all workflow tasks and their status",
                "parameters": {},
                "response": "Array of all tasks with their current status"
            },
            "DELETE /api/clear-tasks": {
                "description": "Clear all completed and failed tasks from memory",
                "parameters": {},
                "response": "Number of tasks cleared"
            }
        },
        
        "file_endpoints": {
            "GET /api/scraping-metadata": {
                "description": "Get the scraping metadata JSON file",
                "parameters": {},
                "response": "Scraping metadata content"
            },
            "GET /api/analysis-results": {
                "description": "Get the SEBI document analysis results JSON file",
                "parameters": {},
                "response": "Analysis results content"
            },
            "GET /api/sebi-circular": {
                "description": "Get extracted content for a specific SEBI circular by reference ID",
                "parameters": {
                    "sebi_circular_ref": "String (required, query parameter) - SEBI circular reference ID (e.g., SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118)"
                },
                "response": "Extracted content including text, markdown, structure, tables, and metadata",
                "example": "GET /api/sebi-circular?sebi_circular_ref=SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118"
            },
            "POST /api/sebi-circular-qa": {
                "description": "Q&A on a single SEBI circular using extracted content and LLM analysis",
                "parameters": {
                    "sebi_circular_ref": "String (required, JSON body) - SEBI circular reference ID",
                    "query": "String (required, JSON body) - Question about the circular content"
                },
                "response": "AI-powered answer based on the circular's extracted content with document metadata",
                "example": "POST /api/sebi-circular-qa with JSON: {\"sebi_circular_ref\": \"SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118\", \"query\": \"What are the key compliance requirements?\"}"
            },
            "GET /api/download-scraping-metadata": {
                "description": "Download the scraping metadata JSON file",
                "parameters": {},
                "response": "File download"
            },
            "GET /api/download-analysis-results": {
                "description": "Download the SEBI document analysis results JSON file",
                "parameters": {},
                "response": "File download"
            }
        },
        
        "database_endpoints": {
            "GET /api/database/tables": {
                "description": "Get all tables in the database with their complete data",
                "parameters": {},
                "response": "All database tables with their records and metadata"
            },
            "GET /api/database/schema": {
                "description": "Get schema information for all database tables",
                "parameters": {},
                "response": "Complete database schema including column types and constraints"
            },
            "GET /api/database/table/<table_name>": {
                "description": "Get data from a specific table with pagination",
                "parameters": {
                    "table_name": "String (required) - Name of the table",
                    "limit": "Integer (optional, default: 100) - Number of records to return",
                    "offset": "Integer (optional, default: 0) - Number of records to skip"
                },
                "response": "Table data with pagination information",
                "allowed_tables": [
                    "teams", "documents", "document_assignments", "actionable_items",
                    "item_assignments", "assignment_timeline", "sebi_analysis_metadata",
                    "sebi_documents", "sebi_key_clauses", "sebi_key_metrics", "sebi_actionable_items"
                ]
            },
            "GET /api/database/summary": {
                "description": "Get a summary of database status and statistics",
                "parameters": {},
                "response": "Database health, table counts, recent activity, and completion statistics"
            }
        },
        
        "chatbot_endpoints": {
            "POST /api/chatbot/chat": {
                "description": "Chat with the SEBI regulatory compliance bot for analysis and insights",
                "parameters": {
                    "query": "String (required) - The question or request to ask the bot",
                    "time_range": "String (optional, default: 'last 1 month') - Time range for document filtering"
                },
                "response": "Structured analysis response with regulatory insights and recommendations",
                "example_queries": [
                    "For stock broker released for last 1 month",
                    "What are the compliance requirements for mutual funds?",
                    "Show me recent changes in trading regulations"
                ]
            }
        },
        
        "table_descriptions": {
            "teams": "Team management data for organizing document assignments",
            "documents": "Document metadata and processing information for general workflow",
            "document_assignments": "Assignment of documents to specific teams",
            "actionable_items": "General actionable items extracted from documents",
            "item_assignments": "Assignment of actionable items to teams",
            "assignment_timeline": "History and timeline of assignment changes",
            "sebi_analysis_metadata": "Metadata for SEBI document analysis workflows",
            "sebi_documents": "SEBI-specific documents with regulatory information",
            "sebi_key_clauses": "Important regulatory clauses extracted from SEBI documents",
            "sebi_key_metrics": "Key metrics and measurements from SEBI documents",
            "sebi_actionable_items": "SEBI-specific actionable items with compliance requirements"
        },
        
        "example_usage": {
            "get_all_data": "GET /api/database/tables",
            "get_table_schema": "GET /api/database/schema",
            "get_specific_table": "GET /api/database/table/sebi_documents?limit=50&offset=0",
            "get_summary": "GET /api/database/summary",
            "get_sebi_circular": "GET /api/sebi-circular?sebi_circular_ref=SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118",
            "sebi_circular_qa": "POST /api/sebi-circular-qa with JSON body: {\"sebi_circular_ref\": \"SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118\", \"query\": \"What are the key compliance requirements?\"}",
            "trigger_workflow": "POST /api/trigger-workflow with JSON body",
            "check_status": "GET /api/workflow-status/{task_id}",
            "chat_with_bot": "POST /api/chatbot/chat with JSON body: {\"query\": \"For stock broker released for last 1 month\"}"
        },
        
        "response_format": {
            "success_response": {
                "status": "success",
                "data": "...",
                "timestamp": "ISO 8601 datetime"
            },
            "error_response": {
                "status": "error",
                "message": "Error description",
                "timestamp": "ISO 8601 datetime"
            }
        }
    }
    
    return jsonify(docs)

if __name__ == "__main__":
    print("🚀 Starting SEBI Document Processing API...")
    print("📖 API Documentation available at: http://localhost:8000/api/docs")
    print("🔧 Health check: http://localhost:8000/")
    print("💾 Database endpoints: http://localhost:8000/api/database/")
    print("📊 Database summary: http://localhost:8000/api/database/summary")
    print("📋 All tables data: http://localhost:8000/api/database/tables")
    print("🏗️ Database schema: http://localhost:8000/api/database/schema")
    print("📄 SEBI circular content: http://localhost:8000/api/sebi-circular?sebi_circular_ref=<ref>")
    print("🤖 SEBI circular Q&A: POST http://localhost:8000/api/sebi-circular-qa")
    print("📁 Scraping metadata: http://localhost:8000/api/scraping-metadata")
    app.run(host="0.0.0.0", port=8000, debug=True)
