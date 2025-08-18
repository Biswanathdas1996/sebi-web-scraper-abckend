from tool.LLM.index import (
        call_pwc_genai
    )
from chatBot.GetContext import (
    get_documents_by_date_range
)
import json


async def chat_bot_response(prompt):
    

    get_context = get_documents_by_date_range(prompt)
    print(json.dumps(get_context, indent=2))
    return
    try:
        # Test ConversationTheme
        theme = await call_pwc_genai(model="vertex_ai.gemini-2.0-flash", prompt="Capital of india")
        result = theme.get('choices', [{}])[0].get('text', '')
        print(result)
        
    except Exception as e:
        print(f"✗ Data class test failed: {e}")


