# Import the LangGraph workflow
from langgraph_workflow import (
    run_custom_sebi_workflow
)

def main():
    
    
    try:
        print("🔧 Running in CUSTOM mode...")
        result = run_custom_sebi_workflow([2])    
        
        # Print final summary
        print("\n" + "="*60)
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"🆔 Workflow ID: {result.get('workflow_id', 'N/A')}")
        print(f"📊 Current Stage: {result.get('current_stage', 'N/A')}")
        print(f"❌ Errors: {len(result.get('errors', []))}")
        print(f"💬 Messages: {len(result.get('messages', []))}")
        
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