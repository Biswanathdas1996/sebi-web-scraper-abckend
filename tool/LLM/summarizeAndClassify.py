import asyncio
import sys
import os
import json

# Add the tool directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tool', 'LLM'))

try:
    from tool.LLM.index import (
        call_pwc_genai
    )
    print("✓ Successfully imported all functions from LLM module")
except ImportError as e:
    print(f"✗ Failed to import LLM functions: {e}")
    sys.exit(1)

async def test_data_classes():
    """Test the data classes"""
    try:
        # Test ConversationTheme
        theme = await call_pwc_genai(model="vertex_ai.gemini-2.0-flash", prompt="Capital of india")
        print(theme)
        
    except Exception as e:
        print(f"✗ Data class test failed: {e}")


async def main():
    """Main test function"""
    print("=== LLM Module Function Test ===")
    await test_data_classes()

if __name__ == "__main__":
    asyncio.run(main())
