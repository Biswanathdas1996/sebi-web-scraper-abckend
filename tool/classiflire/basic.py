import json
import os
import asyncio
from typing import Dict, List, Optional
from ..LLM.index import generate_with_prompt, parse_json_response

# LangSmith tracing
from langsmith import traceable

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
    """Create a structured prompt for analyzing SEBI document content"""
    
    departments_list = "\n".join([f"- {dept}" for dept in DEPARTMENTS])
    intermediaries_list = "\n".join([f"- {inter}" for inter in INTERMEDIARIES])
    
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
    "key_clauses": ["list of important regulatory clauses, provisions, or requirements mentioned"],
    "key_metrics": ["list of numerical metrics, percentages, timelines, or quantitative measures mentioned"],
    "actionable_items": ["list of specific actions, compliance requirements, or implementation steps required"]
}}

AVAILABLE DEPARTMENTS (choose exactly one that best matches):
{departments_list}

AVAILABLE INTERMEDIARIES (choose all that apply from this list):
{intermediaries_list}

INSTRUCTIONS:
1. For "department": Select the EXACT department name from the list above that best matches the issuing authority or subject matter. If no clear match, use "Not Specified".

2. For "intermediary": Include ALL relevant intermediaries from the list above that are mentioned or affected by this document. Use exact names from the list.

3. For "key_clauses": Extract important regulatory provisions, rules, or legal clauses mentioned in the document (max 10).

4. For "key_metrics": Extract specific numbers, percentages, timelines, monetary amounts, or quantitative measures (max 10).

5. For "actionable_items": Extract specific actions, compliance requirements, implementation steps, or obligations mentioned (max 10).

Respond only with valid JSON. Ensure all array items are strings.
"""
    
    return prompt

@traceable(name="analyze_document_content", metadata={"tool": "document_classifier"})
async def analyze_document_content(content: str, filename: str = "") -> Dict:
    
    try:
        prompt = create_analysis_prompt(content)
        
        # Call the LLM with the analysis prompt
        response = await generate_with_prompt(
            prompt=prompt,
            model="vertex_ai.gemini-2.0-flash",
            temperature=0.1,  # Low temperature for consistent analysis
            top_p=0.9
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
