
# SEBI Document Processing Multi-Agent Workflow

## Overview
This LangGraph-based multi-agent system processes SEBI (Securities and Exchange Board of India) documents through a structured workflow with three specialized agents.

## Architecture

### Agents

#### 1. Web Scraping Agent
- **Purpose**: Downloads PDFs from SEBI website using AJAX scraper
- **Input**: Page numbers, download folder
- **Output**: Downloaded PDF files and metadata
- **Technology**: Custom AJAX scraper with session management

#### 2. Document Processing Agent  
- **Purpose**: Extracts text and metadata from PDF documents
- **Input**: Downloaded PDF files
- **Output**: Extracted text content and document metadata
- **Technology**: PyPDF2 and pdfplumber for comprehensive extraction

#### 3. Analysis Agent
- **Purpose**: Analyzes and classifies documents using LLM
- **Input**: Extracted text content
- **Output**: Classified documents with departments, intermediaries, and key insights
- **Technology**: PWC GenAI API with structured prompts

### Workflow Flow

```
START → Web Scraping → [Files Downloaded?] → Document Processing → [Text Extracted?] → Analysis → Finalize → END
           ↓                                        ↓
        [No Files]                              [No Text]
           ↓                                        ↓
        Finalize ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

## State Management

The workflow uses a shared state object that includes:
- Input parameters (page numbers, download folder)
- Results from each stage
- Workflow metadata and error tracking
- Inter-agent messages

## Key Features

### 1. Error Resilience
- Each agent handles errors gracefully
- Workflow continues even if individual stages fail
- Comprehensive error logging and reporting

### 2. Conditional Execution
- Decisions points check if previous stages succeeded
- Workflow can skip stages if prerequisites aren't met
- Smart routing based on intermediate results

### 3. Comprehensive Logging
- Each agent logs its activities with timestamps
- Inter-agent messages track workflow progress
- Final report summarizes entire workflow

### 4. State Persistence
- LangGraph checkpointer maintains workflow state
- Enables workflow resumption and debugging
- Complete audit trail of all operations

## Usage Examples

### Basic Usage
```python
from langgraph_workflow import run_sebi_workflow

# Run with default parameters
result = run_sebi_workflow([1, 2], "test_enhanced_metadata")
```

### Custom Workflow
```python
from langgraph_workflow import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
result = orchestrator.run_workflow([1, 3, 5], "custom_folder")
```

### Original Sequential Comparison
```python
# Original approach (sequential)
result = scrape_page([1,2], "test_enhanced_metadata")
result = process_test_enhanced_metadata_pdfs()
result = run_analysis()

# New approach (multi-agent workflow)
result = run_sebi_workflow([1,2], "test_enhanced_metadata")
```

## Output Files

### Generated Files
1. **scraping_metadata.json** - Raw scraping data and file metadata
2. **sebi_document_analysis_results.json** - LLM analysis results
3. **workflow_results_[ID].json** - Complete workflow execution results

### Metadata Structure
Each file processed includes:
- Circular number and date extraction
- SEBI reference identification  
- Department classification
- Intermediary identification
- Key clauses and metrics
- Actionable items

## Benefits Over Sequential Approach

### 1. Better Error Handling
- Individual stage failures don't crash entire process
- Graceful degradation and recovery mechanisms
- Detailed error reporting and diagnostics

### 2. Improved Observability
- Real-time progress tracking
- Inter-agent communication logging
- Performance metrics and timing

### 3. Enhanced Maintainability
- Modular agent architecture
- Clear separation of concerns
- Easy to extend with new agents

### 4. Workflow Flexibility
- Conditional execution paths
- Configurable parameters
- Multiple workflow patterns supported

## Configuration

### Environment Variables
- API keys for PWC GenAI service
- Custom download paths
- Model selection preferences

### Workflow Parameters
- Page numbers to scrape
- Download folder names
- Processing options
- Analysis model selection

## Monitoring and Debugging

### Logging Levels
- INFO: Normal operation messages
- ERROR: Error conditions and failures
- SUCCESS: Successful stage completions

### State Inspection
- Access to intermediate results
- Workflow state at each stage
- Message history between agents

## Future Enhancements

### Possible Extensions
1. **Parallel Processing Agent** - Process multiple files simultaneously
2. **Validation Agent** - Verify data quality and completeness
3. **Export Agent** - Generate reports in multiple formats
4. **Notification Agent** - Send alerts and updates

### Integration Points
- Database storage for persistent results
- External API integrations
- Workflow scheduling and automation
- Dashboard for workflow monitoring

## Troubleshooting

### Common Issues
1. **Network connectivity** - Check SEBI website accessibility
2. **PDF extraction errors** - Verify file integrity
3. **API failures** - Check PWC GenAI service status
4. **Path issues** - Ensure proper file permissions

### Debug Mode
Enable detailed logging by setting appropriate log levels in each agent.
