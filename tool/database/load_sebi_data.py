"""
Script to initialize SEBI analysis database tables and load data from JSON
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tool.database.sebi_analysis_schema import sebi_db_manager
from tool.database.index import initialize_database


async def initialize_sebi_database():
    """Initialize the SEBI analysis database"""
    print("Initializing base database tables...")
    await initialize_database()
    
    print("Creating SEBI analysis tables...")
    await sebi_db_manager.create_sebi_analysis_tables()
    
    print("Database initialization completed!")


async def load_sebi_analysis_data(json_file_path: str):
    """Load SEBI analysis data from JSON file"""
    print(f"Loading data from {json_file_path}...")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        print(f"Loaded {len(analysis_data.get('documents', []))} documents")
        
        # Insert data into database
        metadata_id = await sebi_db_manager.insert_sebi_analysis_data(analysis_data)
        print(f"Data inserted successfully with metadata ID: {metadata_id}")
        
        # Get summary statistics
        summary = await sebi_db_manager.get_compliance_summary()
        print("\nSummary Statistics:")
        print(f"- Total departments: {len(summary['departments'])}")
        print(f"- Total actionable items: {summary['actionable_items'].get('total_actions', 0)}")
        print(f"- Completed actions: {summary['actionable_items'].get('completed_actions', 0)}")
        print(f"- Recent documents: {summary['recent_documents']}")
        
        # Show department breakdown
        print("\nDepartment breakdown:")
        for dept in summary['departments'][:5]:  # Top 5 departments
            print(f"- {dept['department']}: {dept['doc_count']} documents")
        
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error loading data: {e}")


async def test_database_queries():
    """Test various database queries"""
    print("\n=== Testing Database Queries ===")
    
    # Test department search
    print("\n1. Documents from Investment Management Department:")
    investment_docs = await sebi_db_manager.get_documents_by_department("Investment Management")
    for doc in investment_docs[:3]:  # Show first 3
        print(f"   - {doc['filename']}: {doc['clause_count']} clauses, {doc['actionable_count']} actions")
    
    # Test urgent actionable items
    print("\n2. Most urgent actionable items:")
    urgent_items = await sebi_db_manager.get_actionable_items_by_compliance_urgency()
    for item in urgent_items[:5]:  # Top 5 urgent items
        print(f"   - {item['action_title'][:50]}... (Urgency: {item['urgency_score']})")
    
    # Test search functionality
    print("\n3. Search results for 'mutual fund':")
    search_results = await sebi_db_manager.search_documents("mutual fund")
    for doc in search_results[:3]:  # First 3 results
        print(f"   - {doc['filename']}: {doc['department']}")


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python load_sebi_data.py <command> [json_file_path]")
        print("Commands:")
        print("  init              - Initialize database tables")
        print("  load <json_file>  - Load data from JSON file")
        print("  test              - Test database queries")
        print("  all <json_file>   - Initialize, load data, and test")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "init":
            await initialize_sebi_database()
        
        elif command == "load":
            if len(sys.argv) < 3:
                print("Error: JSON file path required for load command")
                return
            json_file = sys.argv[2]
            await load_sebi_analysis_data(json_file)
        
        elif command == "test":
            await test_database_queries()
        
        elif command == "all":
            if len(sys.argv) < 3:
                print("Error: JSON file path required for all command")
                return
            json_file = sys.argv[2]
            
            await initialize_sebi_database()
            await load_sebi_analysis_data(json_file)
            await test_database_queries()
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
