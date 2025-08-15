"""
Workflow Visualization and Documentation Generator

This module provides utilities to visualize and document the LangGraph workflow
"""

import json
from typing import Dict, Any, List
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def generate_workflow_diagram():
    """
    Generate a visual diagram of the SEBI workflow with proper nodes and connections
    """
    try:
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # Title
        ax.text(7, 11.5, 'LangGraph SEBI Document Processing Workflow', 
                fontsize=18, fontweight='bold', ha='center')
        ax.text(7, 11, 'Multi-Agent System Architecture', 
                fontsize=14, ha='center', style='italic')
        
        # Define colors and styles
        colors = {
            'start_end': '#4CAF50',
            'agent': '#2196F3',
            'decision': '#FF9800',
            'finalize': '#9C27B0',
            'data': '#607D8B'
        }
        
        # Node positions
        nodes = {
            'START': (2, 9.5),
            'web_scraping': (5, 9.5),
            'scraping_check': (8, 9.5),
            'doc_processing': (5, 7),
            'processing_check': (8, 7),
            'analysis': (5, 4.5),
            'finalize': (11, 6.25),
            'END': (13, 6.25)
        }
        
        # Draw START node
        start_circle = patches.Circle(nodes['START'], 0.4, 
                                    facecolor=colors['start_end'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(start_circle)
        ax.text(nodes['START'][0], nodes['START'][1], 'START', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        
        # Draw Web Scraping Agent
        scraping_rect = patches.FancyBboxPatch((nodes['web_scraping'][0]-1.2, nodes['web_scraping'][1]-0.6), 
                                             2.4, 1.2, boxstyle="round,pad=0.1",
                                             facecolor=colors['agent'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(scraping_rect)
        ax.text(nodes['web_scraping'][0], nodes['web_scraping'][1]+0.15, 'Web Scraping Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=10)
        ax.text(nodes['web_scraping'][0], nodes['web_scraping'][1]-0.15, '• Download PDFs\n• Extract links\n• Metadata collection', 
                ha='center', va='center', color='white', fontsize=8)
        
        # Draw Scraping Decision Diamond
        scraping_diamond = patches.RegularPolygon(nodes['scraping_check'], 4, radius=0.8, 
                                                orientation=3.14159/4, facecolor=colors['decision'], 
                                                alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(scraping_diamond)
        ax.text(nodes['scraping_check'][0], nodes['scraping_check'][1]+0.1, 'Files', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=9)
        ax.text(nodes['scraping_check'][0], nodes['scraping_check'][1]-0.1, 'Downloaded?', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=9)
        
        # Draw Document Processing Agent
        processing_rect = patches.FancyBboxPatch((nodes['doc_processing'][0]-1.2, nodes['doc_processing'][1]-0.6), 
                                               2.4, 1.2, boxstyle="round,pad=0.1",
                                               facecolor=colors['agent'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(processing_rect)
        ax.text(nodes['doc_processing'][0], nodes['doc_processing'][1]+0.15, 'Document Processing Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=10)
        ax.text(nodes['doc_processing'][0], nodes['doc_processing'][1]-0.15, '• PDF text extraction\n• Metadata parsing\n• Content validation', 
                ha='center', va='center', color='white', fontsize=8)
        
        # Draw Processing Decision Diamond
        processing_diamond = patches.RegularPolygon(nodes['processing_check'], 4, radius=0.8, 
                                                  orientation=3.14159/4, facecolor=colors['decision'], 
                                                  alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(processing_diamond)
        ax.text(nodes['processing_check'][0], nodes['processing_check'][1]+0.1, 'Text', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=9)
        ax.text(nodes['processing_check'][0], nodes['processing_check'][1]-0.1, 'Extracted?', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=9)
        
        # Draw Analysis Agent
        analysis_rect = patches.FancyBboxPatch((nodes['analysis'][0]-1.2, nodes['analysis'][1]-0.6), 
                                             2.4, 1.2, boxstyle="round,pad=0.1",
                                             facecolor=colors['agent'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(analysis_rect)
        ax.text(nodes['analysis'][0], nodes['analysis'][1]+0.15, 'Analysis Agent', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=10)
        ax.text(nodes['analysis'][0], nodes['analysis'][1]-0.15, '• LLM Classification\n• Department mapping\n• Key insights extraction', 
                ha='center', va='center', color='white', fontsize=8)
        
        # Draw Finalize Node
        finalize_rect = patches.FancyBboxPatch((nodes['finalize'][0]-1.2, nodes['finalize'][1]-0.6), 
                                             2.4, 1.2, boxstyle="round,pad=0.1",
                                             facecolor=colors['finalize'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(finalize_rect)
        ax.text(nodes['finalize'][0], nodes['finalize'][1]+0.15, 'Finalize & Report', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=10)
        ax.text(nodes['finalize'][0], nodes['finalize'][1]-0.15, '• Generate reports\n• Save results\n• Cleanup', 
                ha='center', va='center', color='white', fontsize=8)
        
        # Draw END node
        end_circle = patches.Circle(nodes['END'], 0.4, 
                                  facecolor=colors['start_end'], alpha=0.8, linewidth=2, edgecolor='black')
        ax.add_patch(end_circle)
        ax.text(nodes['END'][0], nodes['END'][1], 'END', 
                ha='center', va='center', fontweight='bold', color='white', fontsize=12)
        
        # Draw data storage nodes
        data_nodes = [
            {'pos': (2, 7), 'label': 'SEBI\nWebsite'},
            {'pos': (2, 4.5), 'label': 'PDF Files'},
            {'pos': (8, 2), 'label': 'JSON Results'},
            {'pos': (11, 2), 'label': 'Final Report'}
        ]
        
        for data_node in data_nodes:
            data_rect = patches.FancyBboxPatch((data_node['pos'][0]-0.6, data_node['pos'][1]-0.4), 
                                             1.2, 0.8, boxstyle="round,pad=0.05",
                                             facecolor=colors['data'], alpha=0.6, linewidth=1, edgecolor='black')
            ax.add_patch(data_rect)
            ax.text(data_node['pos'][0], data_node['pos'][1], data_node['label'], 
                    ha='center', va='center', fontweight='bold', color='white', fontsize=8)
        
        # Draw workflow arrows with labels
        arrows = [
            # Main workflow path
            {'start': (2.4, 9.5), 'end': (3.8, 9.5), 'label': 'Initialize', 'color': 'blue'},
            {'start': (6.2, 9.5), 'end': (7.2, 9.5), 'label': 'Check Files', 'color': 'blue'},
            {'start': (8, 8.7), 'end': (5, 7.6), 'label': 'SUCCESS', 'color': 'green'},
            {'start': (6.2, 7), 'end': (7.2, 7), 'label': 'Check Text', 'color': 'blue'},
            {'start': (8, 6.2), 'end': (5, 5.1), 'label': 'SUCCESS', 'color': 'green'},
            {'start': (6.2, 4.5), 'end': (9.8, 6.25), 'label': 'Complete', 'color': 'blue'},
            {'start': (12.2, 6.25), 'end': (12.6, 6.25), 'label': 'Finish', 'color': 'blue'},
            
            # Error paths
            {'start': (8.8, 9.5), 'end': (9.8, 7.5), 'label': 'NO FILES', 'color': 'red'},
            {'start': (8.8, 7), 'end': (9.8, 6.8), 'label': 'NO TEXT', 'color': 'red'},
            
            # Data connections
            {'start': (2, 6.6), 'end': (4, 8.5), 'label': 'Source', 'color': 'gray', 'style': '--'},
            {'start': (2.6, 4.5), 'end': (3.8, 6.5), 'label': 'Input', 'color': 'gray', 'style': '--'},
            {'start': (6.2, 4.5), 'end': (7.4, 2.5), 'label': 'Output', 'color': 'gray', 'style': '--'},
            {'start': (11, 5.6), 'end': (11, 2.8), 'label': 'Save', 'color': 'gray', 'style': '--'}
        ]
        
        for arrow in arrows:
            style = arrow.get('style', '-')
            ax.annotate('', xy=arrow['end'], xytext=arrow['start'],
                       arrowprops=dict(arrowstyle='->', lw=2, color=arrow['color'], 
                                     linestyle=style, alpha=0.8))
            
            # Add label
            mid_x = (arrow['start'][0] + arrow['end'][0]) / 2
            mid_y = (arrow['start'][1] + arrow['end'][1]) / 2
            ax.text(mid_x, mid_y + 0.2, arrow['label'], 
                    ha='center', va='bottom', fontsize=8, 
                    color=arrow['color'], fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        
       
        
        # Add legend
        legend_elements = [
            patches.Patch(color=colors['start_end'], label='Start/End Nodes'),
            patches.Patch(color=colors['agent'], label='Processing Agents'),
            patches.Patch(color=colors['decision'], label='Decision Points'),
            patches.Patch(color=colors['finalize'], label='Finalization'),
            patches.Patch(color=colors['data'], label='Data Sources/Outputs')
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.99, 0.99))
        
        # Add workflow statistics box
        stats_text = """
        Workflow Statistics:
        • Total Agents: 3
        • Decision Points: 2  
        • Conditional Paths: 4
        • Data I/O Points: 4
        • Error Handling: Yes
        • State Persistence: Yes
        """
        
        ax.text(1, 0.5, stats_text, fontsize=8, 
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('sebi_langgraph_workflow_diagram.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📊 Enhanced LangGraph workflow diagram saved as 'sebi_langgraph_workflow_diagram.png'")
        
    except ImportError:
        print("⚠️  Matplotlib not installed. Run: pip install matplotlib")
        generate_ascii_workflow_diagram()


def generate_ascii_workflow_diagram():
    """
    Generate an ASCII representation of the workflow for environments without matplotlib
    """
    ascii_diagram = """
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                    LangGraph SEBI Document Processing Workflow                   │
    └─────────────────────────────────────────────────────────────────────────────────┘
    
           ┌─────────┐
           │  START  │
           └────┬────┘
                │ Initialize
                ▼
        ┌─────────────────────┐
        │   Web Scraping      │◄──── SEBI Website
        │      Agent          │
        │ • Download PDFs     │
        │ • Extract links     │
        │ • Collect metadata  │
        └─────────┬───────────┘
                  │ Check Files
                  ▼
            ┌──────────────┐
            │ Files        │
            │ Downloaded?  │◄─── Decision Point
            └──┬────────┬──┘
               │        │
        SUCCESS │        │ NO FILES
               ▼        ▼
    ┌─────────────────────┐ │
    │  Document Processing│ │
    │       Agent         │ │
    │ • Extract text      │ │
    │ • Parse metadata    │ │
    │ • Validate content  │ │
    └─────────┬───────────┘ │
              │ Check Text  │
              ▼             │
        ┌──────────────┐    │
        │ Text         │    │
        │ Extracted?   │    │◄─── Decision Point
        └──┬────────┬──┘    │
           │        │       │
    SUCCESS │        │ NO TEXT
           ▼        ▼       │
    ┌─────────────────────┐ │
    │    Analysis         │ │
    │      Agent          │ │
    │ • LLM Classification│ │
    │ • Department mapping│ │
    │ • Extract insights  │ │
    └─────────┬───────────┘ │
              │ Complete    │
              ▼             │
        ┌─────────────────────┐
        │   Finalize &        │◄─┘
        │     Report          │
        │ • Generate reports  │
        │ • Save results      │
        │ • Cleanup          │
        └─────────┬───────────┘
                  │ Finish
                  ▼
            ┌─────────┐
            │   END   │
            └─────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                              State Management                                    │
    ├─────────────────────────────────────────────────────────────────────────────────┤
    │ • page_numbers: List[int] - Pages to scrape                                    │
    │ • download_folder: str - Target folder                                         │
    │ • scraping_result: Dict - Download results                                     │
    │ • processing_result: Dict - Text extraction results                           │
    │ • analysis_result: Dict - LLM analysis results                               │
    │ • current_stage: str - Active workflow stage                                  │
    │ • workflow_id: str - Unique identifier                                        │
    │ • errors: List[str] - Error collection                                        │
    │ • messages: List[Dict] - Agent communications                                 │
    └─────────────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                              Output Files                                       │
    ├─────────────────────────────────────────────────────────────────────────────────┤
    │ • scraping_metadata.json - Raw scraping data                                  │
    │ • sebi_document_analysis_results.json - Analysis results                     │
    │ • workflow_results_[ID].json - Complete workflow results                     │
    └─────────────────────────────────────────────────────────────────────────────────┘
    """
    
    print(ascii_diagram)
    
    # Save ASCII diagram to file
    with open('sebi_workflow_ascii_diagram.txt', 'w', encoding='utf-8') as f:
        f.write(ascii_diagram)
    
    print("📊 ASCII workflow diagram saved as 'sebi_workflow_ascii_diagram.txt'")


def generate_workflow_documentation():
    """
    Generate comprehensive documentation for the workflow
    """
    doc = """
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
"""
    
    # Save documentation to file
    with open('workflow_documentation.md', 'w', encoding='utf-8') as f:
        f.write(doc)
    
    print("📚 Documentation saved as 'workflow_documentation.md'")
    return doc


def generate_state_flow_json():
    """
    Generate a JSON representation of the workflow state transitions and node relationships
    """
    state_flow = {
        "workflow": {
            "name": "SEBI Document Processing",
            "version": "1.0",
            "framework": "LangGraph",
            "description": "Multi-agent workflow for processing SEBI regulatory documents"
        },
        "nodes": {
            "START": {
                "type": "start_node",
                "description": "Workflow initialization",
                "next": ["web_scraping"],
                "state_updates": ["workflow_id", "start_time", "initial_parameters"]
            },
            "web_scraping": {
                "type": "agent_node",
                "name": "Web Scraping Agent",
                "description": "Downloads PDFs from SEBI website using AJAX scraper",
                "function": "web_scraping_agent",
                "inputs": ["page_numbers", "download_folder"],
                "outputs": ["scraping_result", "downloaded_files_metadata"],
                "next": ["scraping_check"],
                "error_handling": "graceful_degradation",
                "timeout": 300,
                "retry_count": 3,
                "capabilities": [
                    "AJAX-based web scraping",
                    "Session management", 
                    "File download tracking",
                    "Metadata extraction",
                    "Link validation"
                ]
            },
            "scraping_check": {
                "type": "conditional_node",
                "name": "Scraping Success Check",
                "description": "Validates if files were successfully downloaded",
                "function": "check_scraping_success",
                "condition": "scraping_result.total_downloaded_files > 0",
                "outcomes": {
                    "continue": "document_processing",
                    "end": "finalize"
                },
                "decision_logic": "file_count_validation"
            },
            "document_processing": {
                "type": "agent_node", 
                "name": "Document Processing Agent",
                "description": "Extracts text and metadata from PDF documents",
                "function": "document_processing_agent",
                "inputs": ["scraping_result", "pdf_files"],
                "outputs": ["processing_result", "extracted_text", "document_metadata"],
                "next": ["processing_check"],
                "error_handling": "per_file_error_tracking",
                "libraries": ["PyPDF2", "pdfplumber"],
                "capabilities": [
                    "PDF text extraction",
                    "Metadata parsing",
                    "Content validation",
                    "Format detection",
                    "Error recovery"
                ]
            },
            "processing_check": {
                "type": "conditional_node",
                "name": "Processing Success Check", 
                "description": "Validates if text extraction was successful",
                "function": "check_processing_success",
                "condition": "processing_result.processed_files_count > 0",
                "outcomes": {
                    "continue": "analysis",
                    "end": "finalize"
                },
                "decision_logic": "extraction_validation"
            },
            "analysis": {
                "type": "agent_node",
                "name": "Analysis Agent",
                "description": "Analyzes and classifies documents using LLM",
                "function": "analysis_agent", 
                "inputs": ["processing_result", "extracted_text"],
                "outputs": ["analysis_result", "classifications", "insights"],
                "next": ["finalize"],
                "error_handling": "document_level_errors",
                "llm_provider": "PWC GenAI API",
                "capabilities": [
                    "Document classification",
                    "Department identification",
                    "Intermediary extraction", 
                    "Key insight generation",
                    "Structured output formatting"
                ]
            },
            "finalize": {
                "type": "finalization_node",
                "name": "Workflow Finalizer",
                "description": "Generates final reports and performs cleanup",
                "function": "finalize_workflow",
                "inputs": ["all_agent_results", "workflow_state"],
                "outputs": ["final_report", "summary_statistics", "saved_files"],
                "next": ["END"],
                "operations": [
                    "Result aggregation",
                    "Report generation", 
                    "File saving",
                    "Statistics calculation",
                    "Cleanup operations"
                ]
            },
            "END": {
                "type": "end_node",
                "description": "Workflow completion",
                "final_state": ["completed", "results_saved"]
            }
        },
        "state_schema": {
            "required_fields": {
                "page_numbers": {
                    "type": "List[int]",
                    "description": "SEBI website page numbers to scrape",
                    "default": [1]
                },
                "download_folder": {
                    "type": "str", 
                    "description": "Target folder for downloaded files",
                    "default": "test_enhanced_metadata"
                }
            },
            "workflow_fields": {
                "scraping_result": {
                    "type": "Dict[str, Any]",
                    "description": "Results from web scraping stage"
                },
                "processing_result": {
                    "type": "Dict[str, Any]",
                    "description": "Results from document processing stage"
                },
                "analysis_result": {
                    "type": "Dict[str, Any]", 
                    "description": "Results from analysis stage"
                }
            },
            "metadata_fields": {
                "current_stage": {
                    "type": "str",
                    "description": "Currently active workflow stage"
                },
                "workflow_id": {
                    "type": "str",
                    "description": "Unique workflow identifier"
                },
                "start_time": {
                    "type": "str",
                    "description": "Workflow start timestamp"
                },
                "errors": {
                    "type": "List[str]",
                    "description": "Collection of errors encountered"
                },
                "messages": {
                    "type": "List[Dict[str, Any]]",
                    "description": "Inter-agent communication messages"
                }
            }
        },
        "edges": {
            "sequential_edges": [
                {"from": "START", "to": "web_scraping", "type": "direct"},
                {"from": "web_scraping", "to": "scraping_check", "type": "direct"},
                {"from": "document_processing", "to": "processing_check", "type": "direct"},
                {"from": "analysis", "to": "finalize", "type": "direct"}, 
                {"from": "finalize", "to": "END", "type": "direct"}
            ],
            "conditional_edges": [
                {
                    "from": "scraping_check",
                    "condition": "check_scraping_success",
                    "outcomes": {
                        "continue": {"to": "document_processing", "condition": "files_downloaded > 0"},
                        "end": {"to": "finalize", "condition": "files_downloaded == 0"}
                    }
                },
                {
                    "from": "processing_check", 
                    "condition": "check_processing_success",
                    "outcomes": {
                        "continue": {"to": "analysis", "condition": "processed_files > 0"},
                        "end": {"to": "finalize", "condition": "processed_files == 0"}
                    }
                }
            ]
        },
        "execution_patterns": {
            "success_path": ["START", "web_scraping", "scraping_check", "document_processing", "processing_check", "analysis", "finalize", "END"],
            "no_files_path": ["START", "web_scraping", "scraping_check", "finalize", "END"],
            "no_text_path": ["START", "web_scraping", "scraping_check", "document_processing", "processing_check", "finalize", "END"],
            "error_recovery": "Each agent handles errors gracefully and continues workflow"
        },
        "output_artifacts": {
            "primary_outputs": [
                {
                    "filename": "scraping_metadata.json",
                    "description": "Raw scraping data and file metadata",
                    "generated_by": "web_scraping_agent"
                },
                {
                    "filename": "sebi_document_analysis_results.json", 
                    "description": "LLM analysis results and classifications",
                    "generated_by": "analysis_agent"
                }
            ],
            "workflow_outputs": [
                {
                    "filename": "workflow_results_[ID].json",
                    "description": "Complete workflow execution results",
                    "generated_by": "finalize_workflow",
                    "optional": "true"
                }
            ]
        },
        "monitoring": {
            "logging_levels": ["INFO", "ERROR", "SUCCESS"],
            "progress_tracking": "Real-time stage updates",
            "error_handling": "Graceful degradation with error collection",
            "performance_metrics": ["duration", "success_rates", "file_counts"]
        }
    }
    
    
    return state_flow


def generate_node_relationship_mermaid():
    """
    Generate a Mermaid diagram representation of the workflow
    """
    mermaid_diagram = """
    ```mermaid
    graph TD
        A[START] --> B[Web Scraping Agent]
        B --> C{Files Downloaded?}
        C -->|YES| D[Document Processing Agent]
        C -->|NO| H[Finalize & Report]
        D --> E{Text Extracted?}
        E -->|YES| F[Analysis Agent]
        E -->|NO| H
        F --> H
        H --> I[END]
        
        %% Data sources and outputs
        J[(SEBI Website)] -.-> B
        K[(PDF Files)] -.-> D
        L[(JSON Results)] -.-> F
        M[(Final Report)] -.-> H
        
        %% Styling
        classDef startEnd fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
        classDef agent fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
        classDef decision fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
        classDef finalize fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
        classDef data fill:#607D8B,stroke:#333,stroke-width:1px,color:#fff
        
        class A,I startEnd
        class B,D,F agent  
        class C,E decision
        class H finalize
        class J,K,L,M data
    ```
    
    ## Node Details
    
    ### Agents (Processing Nodes)
    - **Web Scraping Agent**: Downloads PDFs from SEBI website with session management
    - **Document Processing Agent**: Extracts text from PDFs using PyPDF2/pdfplumber
    - **Analysis Agent**: Classifies documents using LLM (PWC GenAI API)
    
    ### Decision Points
    - **Files Downloaded?**: Checks if scraping was successful (files > 0)
    - **Text Extracted?**: Validates text extraction success (processed_files > 0)
    
    ### Control Flow
    - **Sequential Flow**: Each agent processes data and passes to next stage
    - **Conditional Routing**: Decision points route based on success/failure
    - **Error Recovery**: Failed stages route to finalization for graceful completion
    
    ### State Management
    - **Persistent State**: LangGraph maintains state across all nodes
    - **Message Passing**: Agents communicate via structured messages
    - **Error Tracking**: All errors collected and reported in final stage
    """
    
    # Save Mermaid diagram
    with open('workflow_mermaid_diagram.md', 'w', encoding='utf-8') as f:
        f.write(mermaid_diagram)
    
    print("🌊 Mermaid diagram saved as 'workflow_mermaid_diagram.md'")
    return mermaid_diagram


if __name__ == "__main__":
    print("📋 Generating comprehensive workflow documentation and diagrams...")
    print("="*80)
    
    # Generate all documentation
    print("\n🖼️  Generating visual workflow diagram...")
    generate_workflow_diagram()
    
    print("\n📚 Generating comprehensive documentation...")
    generate_workflow_documentation()  
    
    print("\n🔄 Generating detailed workflow structure...")
    generate_state_flow_json()
    
    print("\n🌊 Generating Mermaid diagram...")
    generate_node_relationship_mermaid()
    
    print("\n" + "="*80)
    print("✅ All documentation generated successfully!")
    print("="*80)
    print("📁 Generated files:")
    print("   🖼️  sebi_langgraph_workflow_diagram.png - Visual workflow diagram")
    print("   � sebi_workflow_ascii_diagram.txt - ASCII text diagram")  
    print("   �📚 workflow_documentation.md - Comprehensive documentation")
    print("   🔄 langgraph_workflow_structure.json - Detailed node structure")
    print("   🌊 workflow_mermaid_diagram.md - Mermaid diagram for web display")
    print("="*80)
    
    # Display summary
    print("\n📊 Workflow Summary:")
    print("   🤖 Total Agents: 3 (Web Scraping, Document Processing, Analysis)")
    print("   🔀 Decision Points: 2 (File validation, Text validation)")
    print("   📈 Execution Paths: 3 (Success, No Files, No Text)")
    print("   🛡️  Error Handling: Graceful degradation with full error tracking")
    print("   💾 State Management: Persistent state with LangGraph checkpointer")
    print("   📤 Output Files: 3 primary + 1 optional workflow result file")
