from chatBot.index import chat_bot_response
import asyncio
import json


async def main():
    """Main test function"""
    print("=== LLM Module Function Test ===")
    response = await chat_bot_response("For stock broker released for last 1 month")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    asyncio.run(main())