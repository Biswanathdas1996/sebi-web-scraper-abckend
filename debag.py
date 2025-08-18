from chatBot.index import chat_bot_response
import asyncio


async def main():
    """Main test function"""
    print("=== LLM Module Function Test ===")
    await chat_bot_response("last 1 month")

if __name__ == "__main__":
    asyncio.run(main())