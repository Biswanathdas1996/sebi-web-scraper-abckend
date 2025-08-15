#!/usr/bin/env python3
"""
Test script to check if the LLM functions are working properly.
"""

import asyncio
import sys
import os
import json

# Add the tool directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tool', 'LLM'))

try:
    from tool.LLM.index import (
        call_pwc_genai, 
        generate_with_prompt, 
        generate_with_custom_parser, 
        parse_json_response,
        PWCModels,
        PWCModel,
        ConversationTheme,
        IndustryMetric
    )
    print("✓ Successfully imported all functions from LLM module")
except ImportError as e:
    print(f"✗ Failed to import LLM functions: {e}")
    sys.exit(1)

async def test_data_classes():
    """Test the data classes"""
    print("\n=== Testing Data Classes ===")
    
    try:
        # Test ConversationTheme
        theme = await call_pwc_genai(model="vertex_ai.gemini-2.0-flash", prompt="Capital of india")
        print(theme)
        
    except Exception as e:
        print(f"✗ Data class test failed: {e}")


async def main():
    """Main test function"""
    print("=== LLM Module Function Test ===")
    
    # Test data classes
    await test_data_classes()
    
   
    
    print("\n=== Test Summary ===")
    print("✓ All basic function tests completed")
    print("⚠ Note: Actual API calls require valid PWC GenAI credentials")
    print("⚠ Set PWC_GENAI_API_KEY and PWC_GENAI_ENDPOINT_URL environment variables for live testing")

if __name__ == "__main__":
    asyncio.run(main())
