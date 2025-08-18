"""
Demo script showing how to use the GetContext.py functions
"""

from chatBot.GetContext import (
    get_documents_by_date_range
)
import json

def demo_usage():
    """
    Demonstrate different ways to use the GetContext functions
    """
    
    
    result = get_documents_by_date_range("last 1 month")
    print(json.dumps(result, indent=2))
    
    
if __name__ == "__main__":
    demo_usage()
   
