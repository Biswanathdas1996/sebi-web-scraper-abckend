"""
LangSmith Configuration Module

This module sets up LangSmith tracing for the SEBI document processing workflow.
It loads environment variables and configures the LangSmith client.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def configure_langsmith() -> bool:
    """
    Configure LangSmith with environment variables
    
    Returns:
        bool: True if LangSmith is properly configured, False otherwise
    """
    try:
        # Check if LangSmith tracing is enabled
        tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        
        if not tracing_enabled:
            print("📊 LangSmith tracing is disabled")
            return False
        
        # Verify required environment variables
        api_key = os.getenv("LANGSMITH_API_KEY")
        endpoint = os.getenv("LANGSMITH_ENDPOINT")
        project = os.getenv("LANGSMITH_PROJECT")
        
        if not api_key:
            print("❌ LANGSMITH_API_KEY not found in environment variables")
            return False
            
        if not endpoint:
            print("❌ LANGSMITH_ENDPOINT not found in environment variables")
            return False
            
        if not project:
            print("❌ LANGSMITH_PROJECT not found in environment variables")
            return False
        
        print("✅ LangSmith configuration:")
        print(f"   🔗 Endpoint: {endpoint}")
        print(f"   📝 Project: {project}")
        print(f"   🔑 API Key: {api_key[:10]}...")
        print("   📊 Tracing: Enabled")
        
        # Set environment variables for LangSmith (in case they weren't set globally)
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to configure LangSmith: {str(e)}")
        return False

def get_langsmith_config() -> dict:
    """
    Get current LangSmith configuration
    
    Returns:
        dict: Configuration dictionary
    """
    return {
        "tracing_enabled": os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        "endpoint": os.getenv("LANGSMITH_ENDPOINT"),
        "project": os.getenv("LANGSMITH_PROJECT"),
        "has_api_key": bool(os.getenv("LANGSMITH_API_KEY"))
    }

def validate_langsmith_setup() -> tuple[bool, list]:
    """
    Validate LangSmith setup and return issues if any
    
    Returns:
        tuple: (is_valid, list_of_issues)
    """
    issues = []
    
    # Check if tracing is enabled
    if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
        issues.append("LANGSMITH_TRACING is not set to 'true'")
    
    # Check required environment variables
    required_vars = ["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGSMITH_PROJECT"]
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"{var} is not set")
    
    # Check API key format (basic validation)
    api_key = os.getenv("LANGSMITH_API_KEY")
    if api_key and not api_key.startswith("lsv2_"):
        issues.append("LANGSMITH_API_KEY appears to have invalid format")
    
    return len(issues) == 0, issues

if __name__ == "__main__":
    # Test the configuration when run directly
    print("🔧 Testing LangSmith Configuration...")
    print("=" * 50)
    
    is_valid, issues = validate_langsmith_setup()
    
    if is_valid:
        configure_langsmith()
        print("✅ LangSmith is properly configured!")
    else:
        print("❌ LangSmith configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease check your .env file and ensure all required variables are set.")
