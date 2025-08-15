# Import the LangGraph workflow
from langgraph_workflow import (
    run_custom_sebi_workflow
)
from langsmith_config import get_langsmith_config

def main():
    # Display LangSmith status
    config = get_langsmith_config()
    print("📊 LangSmith Status:")
    print(f"   Tracing Enabled: {config['tracing_enabled']}")
    if config['tracing_enabled']:
        print(f"   Project: {config['project']}")
        print(f"   Has API Key: {config['has_api_key']}")
    print()
    
    try:
        print("🔧 Running in CUSTOM mode...")
        result = run_custom_sebi_workflow([2])    
        
        if config['tracing_enabled']:
            print(f"📈 LangSmith Project: {config['project']}")
            print("🔗 Check LangSmith dashboard for detailed traces")
        
        if result.get('errors'):
            print("\n⚠️  ERRORS ENCOUNTERED:")
            for i, error in enumerate(result['errors'], 1):
                print(f"   {i}. {error}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Workflow interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {str(e)}")
        return 1



if __name__ == "__main__":
    # If no command line args, run in test mode
    main()