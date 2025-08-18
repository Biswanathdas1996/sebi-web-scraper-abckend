import json
import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import os

def get_documents_by_date_range(time_range_input):
    """
    Filter documents based on circular dates within a specified time range.
    
    Args:
        time_range_input (str): Input like "last 1 month", "last 2 months", etc.
    
    Returns:
        dict: Dictionary containing metadata and filtered documents
        {
            "metadata": {
                "total_filtered_documents": int,
                "filter_criteria": str,
                "date_range": {
                    "from": str,
                    "to": str
                },
                "original_total_documents": int
            },
            "documents": [list of document objects]
        }
    """
    try:
        # Read the JSON file
        file_path = os.path.join(os.path.dirname(__file__), 'output', 'sebi_document_analysis_results.json')
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Parse the time range input
        months = parse_time_range(time_range_input)
        if months is None:
            return {"error": "Invalid time range format. Use format like 'last 1 month', 'last 2 months', etc."}
        
        # Calculate the date range
        current_date = datetime.datetime.now()
        start_date = current_date - relativedelta(months=months)
        
        print(f"Filtering documents from {start_date.strftime('%b %d, %Y')} to {current_date.strftime('%b %d, %Y')}")
        
        # Filter documents
        filtered_documents = []
        
        if 'documents' in data:
            for doc in data['documents']:
                if 'original_metadata' in doc and 'circular_date' in doc['original_metadata']:
                    circular_date_str = doc['original_metadata']['circular_date']
                    
                    # Parse the circular date
                    try:
                        circular_date = parse_circular_date(circular_date_str)
                        
                        if circular_date and start_date <= circular_date <= current_date:
                            filtered_documents.append(doc)
                            
                    except Exception as e:
                        print(f"Error parsing date '{circular_date_str}': {e}")
                        continue
        
        return {
            "metadata": {
                "total_filtered_documents": len(filtered_documents),
                "filter_criteria": time_range_input,
                "date_range": {
                    "from": start_date.strftime('%Y-%m-%d'),
                    "to": current_date.strftime('%Y-%m-%d')
                },
                "original_total_documents": data.get('metadata', {}).get('total_files', 0)
            },
            "documents": filtered_documents
        }
        
    except FileNotFoundError:
        return {"error": "File 'output/sebi_document_analysis_results.json' not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in the file"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

def parse_time_range(time_range_input):
    """
    Parse time range input like "last 1 month", "last 2 months", etc.
    
    Args:
        time_range_input (str): Input string
    
    Returns:
        int: Number of months or None if invalid
    """
    try:
        # Clean and normalize the input
        time_range_input = time_range_input.lower().strip()
        
        # Handle different formats
        if "last" in time_range_input and "month" in time_range_input:
            # Extract number from the string
            words = time_range_input.split()
            for word in words:
                if word.isdigit():
                    return int(word)
                # Handle written numbers
                number_map = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    'eleven': 11, 'twelve': 12
                }
                if word in number_map:
                    return number_map[word]
        
        return None
    except:
        return None

def parse_circular_date(date_str):
    """
    Parse circular date string in various formats.
    
    Args:
        date_str (str): Date string like "Aug 18, 2025" or "Jul 31, 2025"
    
    Returns:
        datetime.datetime: Parsed date or None if parsing fails
    """
    try:
        # Handle common formats found in the data
        if date_str:
            # Try to parse using dateutil parser which handles many formats
            return parser.parse(date_str)
    except:
        return None

def get_document_summary(time_range_input):
    """
    Get a summary of documents in the specified time range.
    
    Args:
        time_range_input (str): Input like "last 1 month", "last 2 months", etc.
    
    Returns:
        dict: Summary information
    """
    result = get_documents_by_date_range(time_range_input)
    
    if "error" in result:
        return result
    
    # Analyze the documents
    departments = {}
    circular_types = {}
    dates = []
    
    for doc in result['documents']:
        # Count departments
        dept = doc.get('department', 'Unknown')
        departments[dept] = departments.get(dept, 0) + 1
        
        # Count intermediaries
        intermediaries = doc.get('intermediary', [])
        for intermediary in intermediaries:
            circular_types[intermediary] = circular_types.get(intermediary, 0) + 1
        
        # Collect dates
        if 'original_metadata' in doc and 'circular_date' in doc['original_metadata']:
            dates.append(doc['original_metadata']['circular_date'])
    
    return {
        "summary": {
            "total_documents": result['metadata']['total_filtered_documents'],
            "date_range": result['metadata']['date_range'],
            "departments": departments,
            "top_intermediary_types": dict(sorted(circular_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "document_dates": dates
        }
    }

def get_documents_by_department(time_range_input, department_name):
    """
    Get documents from a specific department within the time range.
    
    Args:
        time_range_input (str): Input like "last 1 month", "last 2 months", etc.
        department_name (str): Name of the department to filter by
    
    Returns:
        dict: Filtered documents from the specified department
    """
    result = get_documents_by_date_range(time_range_input)
    
    if "error" in result:
        return result
    
    dept_documents = [
        doc for doc in result['documents'] 
        if doc.get('department', '').lower() == department_name.lower()
    ]
    
    return {
        "metadata": {
            **result['metadata'],
            "department_filter": department_name,
            "department_documents_count": len(dept_documents)
        },
        "documents": dept_documents
    }

def get_recent_documents(count=10):
    """
    Get the most recent documents regardless of time range.
    
    Args:
        count (int): Number of recent documents to return
    
    Returns:
        dict: Most recent documents
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'output', 'sebi_document_analysis_results.json')
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        documents_with_dates = []
        
        if 'documents' in data:
            for doc in data['documents']:
                if 'original_metadata' in doc and 'circular_date' in doc['original_metadata']:
                    circular_date_str = doc['original_metadata']['circular_date']
                    try:
                        circular_date = parse_circular_date(circular_date_str)
                        if circular_date:
                            documents_with_dates.append((circular_date, doc))
                    except:
                        continue
        
        # Sort by date (most recent first)
        documents_with_dates.sort(key=lambda x: x[0], reverse=True)
        
        # Get the top 'count' documents
        recent_docs = [doc for _, doc in documents_with_dates[:count]]
        
        return {
            "metadata": {
                "total_recent_documents": len(recent_docs),
                "requested_count": count
            },
            "documents": recent_docs
        }
        
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

