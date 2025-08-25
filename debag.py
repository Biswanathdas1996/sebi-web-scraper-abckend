from tool.GrapgRag.load_data import load_scraping_metadata_to_graph
import asyncio
import json


async def main():
    """Main test function"""
    print("=== LLM Module Function Test ===")
    response = await load_scraping_metadata_to_graph()
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    asyncio.run(main())