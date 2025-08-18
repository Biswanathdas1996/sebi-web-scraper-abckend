# SEBI Document Processing API - Compact Reference

**Base URL:** `http://localhost:5000`

## Quick Reference

| Endpoint                          | Method | Purpose                |
| --------------------------------- | ------ | ---------------------- |
| `/`                               | GET    | Health check           |
| `/api/trigger-workflow`           | POST   | Start workflow         |
| `/api/workflow-status/{task_id}`  | GET    | Check workflow status  |
| `/api/scraping-metadata`          | GET    | Get scraping metadata  |
| `/api/analysis-results`           | GET    | Get analysis results   |
| `/api/download-scraping-metadata` | GET    | Download metadata file |
| `/api/download-analysis-results`  | GET    | Download analysis file |
| `/api/list-tasks`                 | GET    | List all tasks         |
| `/api/clear-tasks`                | DELETE | Clear completed tasks  |

---

## 1. Health Check

```bash
curl -X GET "http://localhost:5000/"
```

**Response:**

```json
{
  "message": "SEBI Document Processing API is running",
  "version": "1.0.0",
  "langsmith_enabled": false,
  "timestamp": "2025-08-16T10:30:00.123456"
}
```

---

## 2. Trigger Workflow

```bash
curl -X POST "http://localhost:5000/api/trigger-workflow" \
     -H "Content-Type: application/json" \
     -d '{
       "page_numbers": [1, 2],
       "download_folder": "test_enhanced_metadata",
       "save_results": true
     }'
```

**Minimal Request:**

```bash
curl -X POST "http://localhost:5000/api/trigger-workflow" \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Success Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initiated",
  "message": "Workflow has been initiated and is running in the background",
  "started_at": "2025-08-16T10:30:00.123456"
}
```

**Error Response:**

```json
{
  "error": "page_numbers must be a list of integers"
}
```

---

## 3. Check Workflow Status

```bash
curl -X GET "http://localhost:5000/api/workflow-status/550e8400-e29b-41d4-a716-446655440000"
```

**Running Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "workflow_id": "sebi_workflow_20250816_103000"
}
```

**Completed Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "workflow_id": "sebi_workflow_20250816_103000",
  "duration": "0:05:30.123456",
  "final_status": "SUCCESS",
  "errors": [],
  "results": {
    "scraping_summary": {
      "pages_processed": 2,
      "files_downloaded": 50,
      "links_found": 50
    },
    "processing_summary": {
      "files_processed": 45,
      "total_files": 50
    },
    "analysis_summary": {
      "documents_analyzed": 45,
      "successful_analyses": 43,
      "failed_analyses": 2
    }
  }
}
```

**Failed Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "workflow_id": "sebi_workflow_20250816_103000",
  "errors": ["Network timeout during scraping"],
  "final_status": "FAILED"
}
```

---

## 4. Get Scraping Metadata

```bash
curl -X GET "http://localhost:5000/api/scraping-metadata"
```

**Response:**

```json
{
  "message": "Scraping metadata retrieved successfully",
  "file_path": "output/scraping_metadata.json",
  "timestamp": "2025-08-16T10:35:00.123456",
  "data": {
    "workflow_id": "sebi_workflow_20250816_103000",
    "timestamp": "2025-08-16T10:30:00.123456",
    "pages_processed": [1, 2],
    "total_links": 50,
    "total_downloaded_files": 45,
    "successful_downloads": 45,
    "failed_downloads": 5,
    "download_folder": "test_enhanced_metadata",
    "scraping_details": [
      {
        "page_number": 1,
        "url": "https://www.sebi.gov.in/web/sebi/reports-and-statistics/reports/annual-reports?pageno=1",
        "links_found": 25,
        "links_downloaded": 23,
        "failed_links": 2,
        "processing_time": "0:02:30.456789"
      }
    ],
    "files": [
      {
        "filename": "page_1_1_Annual_Report_2023.pdf",
        "original_url": "https://www.sebi.gov.in/reports/annual-reports/2023.pdf",
        "file_size": 2048576,
        "download_status": "success"
      }
    ]
  }
}
```

---

## 5. Get Analysis Results

```bash
curl -X GET "http://localhost:5000/api/analysis-results"
```

**Response:**

```json
{
  "message": "Analysis results retrieved successfully",
  "file_path": "output/sebi_document_analysis_results.json",
  "timestamp": "2025-08-16T10:35:00.123456",
  "data": {
    "workflow_id": "sebi_workflow_20250816_103000",
    "analysis_timestamp": "2025-08-16T10:32:00.123456",
    "total_documents": 45,
    "successfully_analyzed": 43,
    "failed_analysis": 2,
    "processing_summary": {
      "total_processing_time": "0:08:45.123456",
      "average_time_per_document": "0:00:12.345678"
    },
    "documents": [
      {
        "filename": "page_1_1_Annual_Report_2023.pdf",
        "file_path": "test_enhanced_metadata/page_1_1_Annual_Report_2023.pdf",
        "analysis_status": "success",
        "processing_time": "0:00:15.123456",
        "content_summary": "This document contains SEBI's annual report for 2023...",
        "key_topics": [
          "Market Regulation",
          "Investor Protection",
          "Corporate Governance"
        ],
        "document_type": "Annual Report",
        "classification": {
          "category": "regulatory_report",
          "subcategory": "annual_report",
          "confidence_score": 0.95
        }
      }
    ],
    "failed_documents": [
      {
        "filename": "corrupted_file.pdf",
        "error": "PDF parsing failed: File appears to be corrupted",
        "error_type": "parsing_error"
      }
    ]
  }
}
```

---

## 6. Download Files

**Download Scraping Metadata:**

```bash
curl -X GET "http://localhost:5000/api/download-scraping-metadata" \
     -o scraping_metadata.json
```

**Download Analysis Results:**

```bash
curl -X GET "http://localhost:5000/api/download-analysis-results" \
     -o sebi_document_analysis_results.json
```

**Response:** Direct file download (JSON file)

---

## 7. List All Tasks

```bash
curl -X GET "http://localhost:5000/api/list-tasks"
```

**Response:**

```json
{
  "message": "Found 3 tasks",
  "timestamp": "2025-08-16T10:40:00.123456",
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "started_at": "2025-08-16T10:30:00.123456",
      "completed_at": "2025-08-16T10:35:30.654321",
      "page_numbers": [1, 2],
      "download_folder": "test_enhanced_metadata",
      "workflow_id": "sebi_workflow_20250816_103000"
    },
    {
      "task_id": "660f9511-f39c-52e5-b827-557766551111",
      "status": "running",
      "started_at": "2025-08-16T10:38:00.123456",
      "page_numbers": [3],
      "download_folder": "test_enhanced_metadata"
    }
  ]
}
```

---

## 8. Clear Completed Tasks

```bash
curl -X DELETE "http://localhost:5000/api/clear-tasks"
```

**Response:**

```json
{
  "message": "Cleared 2 completed/failed tasks",
  "remaining_tasks": 1,
  "timestamp": "2025-08-16T10:42:00.123456"
}
```

---

## Complete Workflow Example

```bash
# 1. Check API health
curl -X GET "http://localhost:5000/"

# 2. Start workflow
TASK_ID=$(curl -s -X POST "http://localhost:5000/api/trigger-workflow" \
  -H "Content-Type: application/json" \
  -d '{"page_numbers": [1], "save_results": true}' | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 3. Monitor progress (repeat until completed/failed)
curl -X GET "http://localhost:5000/api/workflow-status/$TASK_ID"

# 4. Get results when completed
curl -X GET "http://localhost:5000/api/scraping-metadata"
curl -X GET "http://localhost:5000/api/analysis-results"

# 5. Download files
curl -X GET "http://localhost:5000/api/download-scraping-metadata" -o metadata.json
curl -X GET "http://localhost:5000/api/download-analysis-results" -o results.json

# 6. Clean up
curl -X DELETE "http://localhost:5000/api/clear-tasks"
```

---

## Status Codes

- **200**: Success
- **400**: Bad Request (validation error)
- **404**: Not Found (task/file not found)
- **500**: Internal Server Error

## Error Format

```json
{
  "error": "Error description"
}
```

## Request Payload Schema

**Trigger Workflow:**

```json
{
  "page_numbers": [1, 2, 3], // optional, default: [1]
  "download_folder": "folder_name", // optional, default: "test_enhanced_metadata"
  "save_results": true // optional, default: true
}
```

---

**Note:** Replace `http://localhost:5000` with your actual server URL and port.
