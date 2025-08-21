import json
import os
import asyncio
from typing import Dict, List, Optional
from ..LLM.index import generate_with_prompt, parse_json_response

# LangSmith tracing
from langsmith import traceable

teams = [
  {
    "id": "148ab232-7196-4e85-8a30-d28a33d51003",
    "name": "Finance",
    "type": "finance",
    "description": "Manages financial compliance and reporting requirements"
  },
  {
    "id": "1bbaf0a8-4690-4d70-a918-2ce6e46f3b2b",
    "name": "Executive",
    "type": "executive",
    "description": "Executive oversight and strategic decisions"
  },
  {
    "id": "ac9c0edf-6c0e-4ec0-ab02-6405843702f2",
    "name": "Operations",
    "type": "operations",
    "description": "Handles day-to-day operational activities and implementations"
  },
  {
    "id": "c5cf11f5-d691-4cf9-b986-5a6f62409b29",
    "name": "Risk Management",
    "type": "risk_management",
    "description": "Manages operational and strategic risks"
  },
  {
    "id": "f0cad2c1-77a0-432e-a458-2603d214fb82",
    "name": "Legal & Compliance",
    "type": "legal_compliance",
    "description": "Handles legal matters, regulatory compliance, and policy interpretation"
  }
]

# Define the available options for classification
DEPARTMENTS = [
    "Alternative Investment Fund and Foreign Portfolio Investors Department",
    "Corporation Finance Department", 
    "Department Economic and Policy Analysis",
    "Department of Debt and Hybrid Securities",
    "Enforcement Department - 1",
    "Information Technology Department",
    "Investment Management Department",
    "Market Intermediaries Regulation and Supervision Department",
    "Market Regulation Department",
    "Office of Investor Assistance and Education"
]

INTERMEDIARIES = [
    "Banker to an Issue",
    "Debentures Trustee",
    "Credit Rating Agency - CRA",
    "KYC (Know Your Client) Registration Agency registered with SEBI",
    "Merchant Bankers",
    "Registrars to an issue and share Transfer Agents",
    "Underwriters",
    "Registered Alternative Investment Funds",
    "Registered Venture Capital Funds",
    "Registered Mutual Funds",
    "Registered Foreign Venture Capital Investors",
    "Registered Custodians",
    "Deemed FPIs (Erstwhile Sub-Accounts)",
    "FPIs / Deemed FPIs (Erstwhile FIIs/QFIs)",
    "Registered Stock Brokers in equity segment",
    "Registered Stock Brokers in Equity Derivative Segment",
    "Registered Stock Brokers in Currency Derivative Segment",
    "Registered Portfolio Managers",
    "Self-Certified Syndicate Banks under the direct ASBA facility (equity issuances)"
]

def create_analysis_prompt(content: str) -> str:
    """
    Create a comprehensive structured prompt for analyzing SEBI document content.
    
    This function generates an enhanced prompt that ensures thorough regulatory analysis
    with detailed extraction of:
    - Structured key clauses with compliance impact analysis
    - Comprehensive key metrics with full contextual information  
    - Detailed actionable items with implementation requirements and team assignments
    
    The prompt is designed to capture every regulatory detail to ensure
    complete compliance analysis for SEBI regulatory documents.
    
    Args:
        content (str): The SEBI document content to analyze
        
    Returns:
        str: Enhanced analysis prompt for comprehensive regulatory extraction
    """
    
    departments_list = "\n".join([f"- {dept}" for dept in DEPARTMENTS])
    intermediaries_list = "\n".join([f"- {inter}" for inter in INTERMEDIARIES])
    teams_list = "\n".join([f"- {team['name']} ({team['type']}): {team['description']}" for team in teams])
    
    prompt = f"""
You are an expert analyst specializing in SEBI (Securities and Exchange Board of India) regulatory documents. 
Analyze the following SEBI circular/document content and extract key information in a structured JSON format.

DOCUMENT CONTENT:
{content}  # Limit content to avoid token limits

ANALYSIS REQUIREMENTS:
Based on the document content, provide a JSON response with the following structure:

{{
    "department": "exact match from the list below or 'Not Specified'",

    "intermediary": ["list of exact matches from the intermediaries list below, or empty array if none apply"],
    "summary": "concise 2-3 sentence summary of the document's main purpose and key points",
    "key_clauses": [
        {{
            "clause_title": "descriptive title of the regulatory provision",
            "clause_content": "detailed description of the regulatory clause or requirement",
            "regulatory_impact": "explanation of how this clause impacts regulated entities",
            "compliance_level": "mandatory/advisory/conditional",
            "effective_date": "when this clause becomes effective (if specified)",
            "penalty_consequences": "penalties or consequences for non-compliance (if mentioned)"
        }}
    ],
    "key_metrics": [
        {{
            "metric_type": "type of metric (percentage, amount, timeline, ratio, etc.)",
            "metric_value": "actual numerical value or range",
            "metric_description": "detailed context and significance of this metric",
            "applicable_entities": "which intermediaries or entities this metric applies to",
            "calculation_method": "how the metric is calculated or determined (if specified)",
            "reporting_frequency": "how often this metric needs to be reported (if applicable)",
            "threshold_significance": "what happens when this threshold is met/exceeded"
        }}
    ],
    "actionable_items": [
        {{
            "action_title": "clear title of the required action",
            "action_description": "comprehensive description of what needs to be done",
            "responsible_parties": "who is responsible for implementing this action",
            "implementation_timeline": "specific deadlines, timelines, or effective dates",
            "compliance_requirements": "detailed compliance obligations and standards",
            "documentation_needed": "required documentation, forms, or submissions",
            "monitoring_mechanism": "how compliance will be monitored or verified",
            "non_compliance_consequences": "specific penalties or actions for non-compliance",
            "assigned_team": {{
                "id": "team UUID from the teams list",
                "name": "exact team name from the teams list",
                "type": "team type from the teams list",
                "description": "team description from the teams list"
            }}
        }}
    ]
}}

AVAILABLE DEPARTMENTS (choose exactly one that best matches):
{departments_list}

AVAILABLE INTERMEDIARIES (choose all that apply from this list):
{intermediaries_list}

AVAILABLE TEAMS (assign the most appropriate team for each actionable item):
{teams_list}

INSTRUCTIONS:
1. For "department": Select the EXACT department name from the list above that best matches the issuing authority or subject matter. If no clear match, use "Not Specified".

2. For "intermediary": Include ALL relevant intermediaries from the list above that are mentioned or affected by this document. Use exact names from the list.

3. For "summary": Provide a concise 2-3 sentence summary capturing the document's main purpose, key regulatory changes, or primary subject matter.

4. For "key_clauses": Extract ALL important regulatory provisions, rules, or legal clauses as structured objects. For each clause, provide:
   - A descriptive title that clearly identifies the provision
   - Detailed content explaining the regulatory requirement
   - Analysis of regulatory impact on affected entities
   - Classification as mandatory, advisory, or conditional
   - Effective date if specified
   - Any mentioned penalties or consequences for non-compliance
   Include every significant regulatory provision - do not summarize or skip important clauses.

5. For "key_metrics": Extract ALL numerical data, quantitative measures, and metrics as structured objects. Include:
   - Percentages, ratios, monetary amounts, timelines, thresholds
   - Detailed context explaining the significance of each metric
   - Which entities or intermediaries the metric applies to
   - Calculation methodologies if provided
   - Reporting frequencies and requirements
   - Consequences of meeting or exceeding thresholds
   Leave no quantitative data unanalyzed - capture every number with its full context.

6. For "actionable_items": Extract ALL specific actions, obligations, and implementation requirements as detailed structured objects. For each item, provide:
   - Clear title describing the required action
   - Comprehensive description of implementation requirements
   - Identification of responsible parties or entities
   - Specific timelines, deadlines, and effective dates
   - Detailed compliance obligations and standards
   - Required documentation, forms, or submissions
   - How compliance will be monitored or verified
   - Specific consequences for non-compliance
   - Assigned team: Select the most appropriate team from the teams list and include the complete team object (id, name, type, description)
   Ensure no compliance requirement or implementation step is missed - this is critical for regulatory adherence.

7. For "assigned_team" in actionable items: Analyze the nature of each actionable item and assign it to the most appropriate team. Include the COMPLETE team object with all fields (id, name, type, description) exactly as provided in the teams list:
   - Finance (id: 148ab232-7196-4e85-8a30-d28a33d51003): For financial compliance, reporting requirements, monetary obligations
   - Executive (id: 1bbaf0a8-4690-4d70-a918-2ce6e46f3b2b): For strategic decisions, high-level policy changes, board-level approvals
   - Operations (id: ac9c0edf-6c0e-4ec0-ab02-6405843702f2): For day-to-day implementation, operational procedures, system changes
   - Risk Management (id: c5cf11f5-d691-4cf9-b986-5a6f62409b29): For risk assessment, mitigation strategies, compliance monitoring
   - Legal & Compliance (id: f0cad2c1-77a0-432e-a458-2603d214fb82): For legal interpretations, regulatory compliance, policy documentation

CRITICAL REGULATORY ANALYSIS INSTRUCTIONS:
- This is a regulatory document analysis where completeness is paramount
- Every regulatory provision, numerical metric, and action item must be captured
- Do not summarize or paraphrase - provide complete, detailed information
- Pay special attention to:
  * Effective dates and deadlines
  * Penalty clauses and enforcement mechanisms
  * Compliance thresholds and reporting requirements
  * Exemptions, conditions, and special circumstances
  * Amendment or modification of existing regulations
  * Transition periods and implementation phases
- If uncertain about categorization, err on the side of inclusion rather than exclusion
- Maintain the exact terminology and phrasing used in the regulatory document

Respond only with valid JSON. Ensure all nested objects follow the specified structure exactly.
"""
    
    return prompt

@traceable(name="analyze_document_content", metadata={"tool": "document_classifier"})
async def analyze_document_content(content: str, filename: str = "") -> Dict:
    
    try:
        prompt = create_analysis_prompt(content)
        
        # Call the LLM with the enhanced analysis prompt
        # Using low temperature for consistent regulatory analysis
        # and high top_p for comprehensive information extraction
        response = await generate_with_prompt(
            prompt=prompt,
            model="vertex_ai.gemini-2.0-flash",
            temperature=0.1,  # Low temperature for consistent regulatory analysis
            top_p=0.95  # Increased for more comprehensive extraction
        )
        
        # Parse the JSON response
        analysis = parse_json_response(response)
        
        # Add metadata
        analysis["filename"] = filename
        analysis["content_length"] = len(content)
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing document {filename}: {str(e)}")
        return {
            "filename": filename,
            "department": "Analysis Failed",
            "intermediary": [],
            "key_clauses": [],
            "key_metrics": [],
            "actionable_items": [],
            "error": str(e)
        }

@traceable(name="process_scraping_metadata", metadata={"tool": "sebi_document_processor"})
async def process_scraping_metadata() -> Dict:
    """
    Main function to process scraping_metadata.json file and analyze all documents
    
    Returns:
        Dict: Complete analysis results for all documents
    """
    
    # Load the scraping metadata
    metadata_path = os.path.join(os.getcwd(), "output", "scraping_metadata.json")
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"scraping_metadata.json not found in current directory")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Extract files information from all page results
    page_results = metadata.get('page_results', [])
    files_info = []
    for page_result in page_results:
        if 'files' in page_result:
            files_info.extend(page_result['files'])
    
    if not files_info:
        raise ValueError("No files found in scraping_metadata.json")
     
    print(f"Found {len(files_info)} files to analyze...")
    
    # Results storage
    analysis_results = {
        "metadata": {
            "total_files": len(files_info),
            "scrape_timestamp": metadata.get('scrape_timestamp'),
            "analysis_timestamp": None
        },
        "documents": []
    }
    
    # Process each file
    for i, file_info in enumerate(files_info, 1):
        print(f"Processing file {i}/{len(files_info)}: {file_info.get('original_filename', 'Unknown')}")
        
        try:
            # Get extracted content
            extracted_content = file_info.get('extracted_content', {})
            text_content = extracted_content.get('text', '')
            
            if not text_content:
                print(f"Warning: No text content found for {file_info.get('original_filename')}")
                continue
            
            # Analyze the document
            analysis = await analyze_document_content(
                content=text_content,
                filename=file_info.get('original_filename', f"file_{i}")
            )
            
            # Add original file metadata
            analysis["original_metadata"] = {
                "circular_number": file_info.get('circular_number'),
                "circular_date": file_info.get('circular_date'),
                "url": file_info.get('url'),
                "source_url": file_info.get('source_url'),
                "link_text": file_info.get('link_text')
            }
            
            analysis_results["documents"].append(analysis)
            
        except Exception as e:
            print(f"Error processing file {file_info.get('original_filename')}: {str(e)}")
            error_analysis = {
                "filename": file_info.get('original_filename'),
                "department": "Processing Failed",
                "intermediary": [],
                "key_clauses": [],
                "key_metrics": [],
                "actionable_items": [],
                "error": str(e),
                "original_metadata": {
                    "circular_number": file_info.get('circular_number'),
                    "circular_date": file_info.get('circular_date'),
                    "url": file_info.get('url'),
                    "source_url": file_info.get('source_url'),
                    "link_text": file_info.get('link_text')
                }
            }
            analysis_results["documents"].append(error_analysis)
    
    # Add analysis timestamp
    from datetime import datetime
    analysis_results["metadata"]["analysis_timestamp"] = datetime.now().isoformat()
    
    # Save results to JSON file
    output_filename = "output/sebi_document_analysis_results.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis complete! Results saved to {output_filename}")
    print(f"Successfully analyzed {len([doc for doc in analysis_results['documents'] if 'error' not in doc])} documents")
    print(f"Failed to analyze {len([doc for doc in analysis_results['documents'] if 'error' in doc])} documents")
    
    return analysis_results

@traceable(name="run_analysis", metadata={"workflow_stage": "document_analysis"})
def run_analysis():
    """
    Synchronous wrapper function to run the analysis
    """
    return asyncio.run(process_scraping_metadata())

# Export the main functions
__all__ = [
    'process_scraping_metadata',
    'analyze_document_content',
    'run_analysis'
]
