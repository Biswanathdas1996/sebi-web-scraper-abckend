from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from typing import List, Dict, Any, Optional
import os
import json
import threading
from datetime import datetime
import uuid

# Import the LangGraph workflow
from langgraph_workflow import run_custom_sebi_workflow
from langsmith_config import get_langsmith_config

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
        "timestamp": datetime.now().isoformat()
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

if __name__ == "__main__":
    print("🚀 Starting SEBI Document Processing API...")
    print("📖 API Documentation available at: http://localhost:8000/")
    print("🔧 Health check: http://localhost:8000/")
    app.run(host="0.0.0.0", port=8000, debug=True)
