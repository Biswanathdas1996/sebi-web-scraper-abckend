"""
Standalone Database Loader Script for SEBI Document Analysis
This script can be used to load analyzed SEBI document data into the database
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import database managers
from tool.database.index import db_manager, initialize_database
from tool.database.sebi_analysis_schema import sebi_db_manager


class SEBIDataLoader:
    """Standalone loader for SEBI analysis data"""
    
    def __init__(self):
        self.loaded_count = 0
        self.error_count = 0
        self.errors = []
    
    async def initialize_database(self):
        """Initialize database tables"""
        print("🔧 Initializing database tables...")
        try:
            await db_manager.create_tables()
            await sebi_db_manager.create_sebi_analysis_tables()
            print("✅ Database tables initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            raise
    
    async def load_json_file(self, file_path: str) -> dict:
        """Load a single JSON file into the database"""
        print(f"📄 Loading file: {file_path}")
        
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Validate data structure
            if not self._validate_data_structure(analysis_data):
                raise ValueError("Invalid data structure in JSON file")
            
            # Load into database
            metadata_id = await sebi_db_manager.insert_sebi_analysis_data(analysis_data)
            
            result = {
                "success": True,
                "metadata_id": metadata_id,
                "file_path": file_path,
                "total_documents": len(analysis_data.get("documents", [])),
                "loaded_at": datetime.now().isoformat()
            }
            
            self.loaded_count += 1
            print(f"✅ Successfully loaded {result['total_documents']} documents with metadata ID: {metadata_id}")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Failed to load {file_path}: {str(e)}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "loaded_at": datetime.now().isoformat()
            }
    
    async def load_directory(self, directory_path: str, pattern: str = "*.json") -> list:
        """Load all JSON files from a directory"""
        print(f"📁 Loading all {pattern} files from: {directory_path}")
        
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        json_files = list(directory.glob(pattern))
        if not json_files:
            print(f"⚠️  No {pattern} files found in {directory_path}")
            return []
        
        print(f"🔍 Found {len(json_files)} files to process")
        
        results = []
        for file_path in json_files:
            result = await self.load_json_file(str(file_path))
            results.append(result)
        
        return results
    
    async def get_database_status(self) -> dict:
        """Get current database status and statistics"""
        print("📊 Retrieving database status...")
        
        try:
            # Health check
            health = await db_manager.health_check()
            
            # SEBI compliance summary
            compliance = await sebi_db_manager.get_compliance_summary()
            
            # Team workload
            workload = await db_manager.get_team_workload_summary()
            
            return {
                "database_health": health,
                "sebi_compliance": compliance,
                "team_workload": workload,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get database status: {e}")
            return {"error": str(e)}
    
    def _validate_data_structure(self, data: dict) -> bool:
        """Validate the structure of analysis data"""
        required_keys = ["metadata", "documents"]
        
        if not all(key in data for key in required_keys):
            return False
        
        if not isinstance(data["documents"], list):
            return False
        
        # Validate at least one document has the required structure
        if data["documents"]:
            doc = data["documents"][0]
            doc_required = ["filename", "department", "summary"]
            if not any(key in doc for key in doc_required):
                return False
        
        return True
    
    def print_summary(self):
        """Print loading summary"""
        print("\n" + "="*60)
        print("📈 LOADING SUMMARY")
        print("="*60)
        print(f"✅ Successfully loaded: {self.loaded_count} files")
        print(f"❌ Failed: {self.error_count} files")
        
        if self.errors:
            print("\n🔍 ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        print("="*60)


async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Load SEBI analysis data into database")
    parser.add_argument("--file", "-f", help="Path to JSON file to load")
    parser.add_argument("--directory", "-d", help="Path to directory containing JSON files")
    parser.add_argument("--pattern", "-p", default="*.json", help="File pattern to match (default: *.json)")
    parser.add_argument("--status", "-s", action="store_true", help="Show database status")
    parser.add_argument("--init", action="store_true", help="Initialize database tables only")
    
    args = parser.parse_args()
    
    loader = SEBIDataLoader()
    
    try:
        # Initialize database
        await loader.initialize_database()
        
        if args.init:
            print("✅ Database initialization completed")
            return
        
        if args.status:
            status = await loader.get_database_status()
            print("\n📊 DATABASE STATUS:")
            print(json.dumps(status, indent=2, default=str))
            return
        
        results = []
        
        if args.file:
            # Load single file
            result = await loader.load_json_file(args.file)
            results.append(result)
        
        elif args.directory:
            # Load directory
            results = await loader.load_directory(args.directory, args.pattern)
        
        else:
            # Default: load from output directory
            output_dir = project_root / "output"
            if output_dir.exists():
                print(f"📁 No specific path provided, loading from default output directory: {output_dir}")
                results = await loader.load_directory(str(output_dir))
            else:
                print("❌ No file or directory specified, and default output directory not found")
                parser.print_help()
                return
        
        # Print summary
        loader.print_summary()
        
        # Save results
        if results:
            results_file = project_root / f"database_loading_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Detailed results saved to: {results_file}")
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


# Additional utility functions for interactive use

async def quick_load_output_directory():
    """Quick function to load all files from output directory"""
    loader = SEBIDataLoader()
    await loader.initialize_database()
    
    output_dir = Path(__file__).parent / "output"
    if output_dir.exists():
        results = await loader.load_directory(str(output_dir))
        loader.print_summary()
        return results
    else:
        print("❌ Output directory not found")
        return []


async def load_sample_file():
    """Load the sample analysis results file"""
    loader = SEBIDataLoader()
    await loader.initialize_database()
    
    sample_file = Path(__file__).parent / "output" / "sebi_document_analysis_results.json"
    if sample_file.exists():
        result = await loader.load_json_file(str(sample_file))
        loader.print_summary()
        return result
    else:
        print("❌ Sample file not found")
        return None


async def show_database_summary():
    """Show comprehensive database summary"""
    loader = SEBIDataLoader()
    status = await loader.get_database_status()
    print(json.dumps(status, indent=2, default=str))
    return status


if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
