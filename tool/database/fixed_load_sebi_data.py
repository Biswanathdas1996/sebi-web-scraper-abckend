"""
SEBI data loader with table recreation to fix field sizes
"""

import json
import asyncio
import asyncpg
import os
from datetime import datetime
from typing import Dict, Any
import uuid

# Database connection
DATABASE_URL = "postgresql://neondb_owner:npg_2aZoeNujTmA5@ep-bold-dawn-adz91n9q.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def drop_and_recreate_tables(conn):
    """Drop existing SEBI tables and recreate them with correct field sizes"""
    
    print("🗑️  Dropping existing SEBI tables...")
    
    # Drop tables in reverse order due to foreign key constraints
    drop_queries = [
        "DROP TABLE IF EXISTS sebi_actionable_items CASCADE;",
        "DROP TABLE IF EXISTS sebi_key_metrics CASCADE;",
        "DROP TABLE IF EXISTS sebi_key_clauses CASCADE;",
        "DROP TABLE IF EXISTS sebi_documents CASCADE;",
        "DROP TABLE IF EXISTS sebi_analysis_metadata CASCADE;",
        "DROP TYPE IF EXISTS compliance_level CASCADE;",
        "DROP TYPE IF EXISTS metric_type CASCADE;"
    ]
    
    for query in drop_queries:
        try:
            await conn.execute(query)
        except Exception as e:
            print(f"Note: {e}")
    
    print("✅ Tables dropped successfully")
    
    # Create enums
    print("🔧 Creating enums...")
    await conn.execute("""
        CREATE TYPE compliance_level AS ENUM ('mandatory', 'conditional', 'advisory', 'informational');
    """)
    
    await conn.execute("""
        CREATE TYPE metric_type AS ENUM ('timeline', 'amount', 'count', 'percentage', 'rate', 'other');
    """)
    
    # Main analysis results table
    print("🏗️  Creating sebi_analysis_metadata table...")
    await conn.execute("""
        CREATE TABLE sebi_analysis_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            total_files INTEGER NOT NULL,
            scrape_timestamp TIMESTAMP WITH TIME ZONE,
            analysis_timestamp TIMESTAMP WITH TIME ZONE,
            workflow_id VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    
    # Documents table
    print("🏗️  Creating sebi_documents table...")
    await conn.execute("""
        CREATE TABLE sebi_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            analysis_metadata_id UUID REFERENCES sebi_analysis_metadata(id),
            filename VARCHAR(255) NOT NULL,
            title TEXT,
            department VARCHAR(200),
            summary TEXT,
            content_length INTEGER,
            intermediary TEXT[],
            circular_number VARCHAR(100),
            circular_date DATE,
            source_url TEXT,
            link_text TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    
    # Key clauses table
    print("🏗️  Creating sebi_key_clauses table...")
    await conn.execute("""
        CREATE TABLE sebi_key_clauses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES sebi_documents(id) ON DELETE CASCADE,
            clause_title VARCHAR(500) NOT NULL,
            clause_content TEXT NOT NULL,
            regulatory_impact TEXT,
            compliance_level compliance_level DEFAULT 'mandatory',
            effective_date DATE,
            penalty_consequences TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    
    # Key metrics table with larger field sizes
    print("🏗️  Creating sebi_key_metrics table...")
    await conn.execute("""
        CREATE TABLE sebi_key_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES sebi_documents(id) ON DELETE CASCADE,
            metric_type metric_type NOT NULL,
            metric_value TEXT NOT NULL,
            metric_description TEXT NOT NULL,
            applicable_entities TEXT,
            calculation_method TEXT,
            reporting_frequency TEXT,
            threshold_significance TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    
    # Actionable items table
    print("🏗️  Creating sebi_actionable_items table...")
    await conn.execute("""
        CREATE TABLE sebi_actionable_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES sebi_documents(id) ON DELETE CASCADE,
            action_title VARCHAR(1000) NOT NULL,
            action_description TEXT,
            responsible_parties TEXT,
            implementation_timeline TEXT,
            compliance_requirements TEXT,
            documentation_needed TEXT,
            monitoring_mechanism TEXT,
            non_compliance_consequences TEXT,
            is_completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    
    print("✅ All tables recreated successfully!")

def map_metric_type(metric_type: str) -> str:
    """Map metric type to valid enum values"""
    if not metric_type:
        return "other"
    
    # Convert to lowercase for comparison
    metric_lower = metric_type.lower()
    
    # Map to valid enum values
    valid_types = ["timeline", "amount", "count", "percentage", "rate", "other"]
    
    # Direct mapping
    if metric_lower in valid_types:
        return metric_lower
    
    # Handle variations
    if "reporting frequency" in metric_lower:
        return "rate"  # Use rate for frequency
    elif "timeline" in metric_lower:
        return "timeline"
    elif "percentage" in metric_lower or "%" in metric_lower:
        return "percentage"
    elif "amount" in metric_lower or "value" in metric_lower:
        return "amount"
    elif "count" in metric_lower or "number" in metric_lower:
        return "count"
    elif "rate" in metric_lower or "frequency" in metric_lower:
        return "rate"
    else:
        return "other"

def map_compliance_level(compliance_level: str) -> str:
    """Map compliance level to valid enum values"""
    if not compliance_level:
        return "informational"
    
    # Convert to lowercase for comparison
    compliance_lower = compliance_level.lower()
    
    # Valid enum values: "mandatory", "conditional", "advisory", "informational"
    valid_levels = ["mandatory", "conditional", "advisory", "informational"]
    
    # Direct mapping
    if compliance_lower in valid_levels:
        return compliance_lower
    
    # Handle variations and edge cases
    if "n/a" in compliance_lower or "sebi initiative" in compliance_lower or "na" in compliance_lower:
        return "informational"
    elif "must" in compliance_lower or "required" in compliance_lower or "shall" in compliance_lower:
        return "mandatory"
    elif "should" in compliance_lower or "recommended" in compliance_lower:
        return "advisory"
    elif "may" in compliance_lower or "optional" in compliance_lower or "if" in compliance_lower:
        return "conditional"
    else:
        return "informational"

async def load_sebi_json_to_database(json_file_path: str) -> str:
    """
    Load SEBI document analysis results from JSON file into the database
    
    Args:
        json_file_path (str): Path to the sebi_document_analysis_results.json file
        
    Returns:
        str: The metadata_id of the inserted analysis data
    """
    
    # Read the JSON file
    print(f"📖 Reading JSON file: {json_file_path}")
    
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as file:
        analysis_data = json.load(file)
    
    print(f"✓ Successfully loaded JSON with {len(analysis_data.get('documents', []))} documents")
    
    # Connect to database
    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Drop and recreate tables
        await drop_and_recreate_tables(conn)
        
        # Start transaction
        async with conn.transaction():
            # Insert metadata
            metadata_id = str(uuid.uuid4())
            metadata = analysis_data.get('metadata', {})
            
            # Parse timestamps
            scrape_timestamp = None
            analysis_timestamp = None
            
            if metadata.get('scrape_timestamp'):
                try:
                    scrape_timestamp = datetime.fromisoformat(metadata['scrape_timestamp'].replace('Z', '+00:00'))
                except:
                    pass
            
            if metadata.get('analysis_timestamp'):
                try:
                    analysis_timestamp = datetime.fromisoformat(metadata['analysis_timestamp'].replace('Z', '+00:00'))
                except:
                    pass
            
            await conn.execute("""
                INSERT INTO sebi_analysis_metadata (id, total_files, scrape_timestamp, analysis_timestamp)
                VALUES ($1, $2, $3, $4)
            """, metadata_id, metadata.get('total_files', 0), scrape_timestamp, analysis_timestamp)
            
            print(f"✓ Inserted metadata with ID: {metadata_id}")
            
            # Insert documents and related data
            documents = analysis_data.get('documents', [])
            for i, doc_data in enumerate(documents):
                print(f"📄 Processing document {i+1}/{len(documents)}: {doc_data.get('filename', 'Unknown')}")
                
                document_id = await insert_document(conn, metadata_id, doc_data)
                
                # Insert key clauses
                for clause in doc_data.get('key_clauses', []):
                    await insert_key_clause(conn, document_id, clause)
                
                # Insert key metrics
                for metric in doc_data.get('key_metrics', []):
                    await insert_key_metric(conn, document_id, metric)
                
                # Insert actionable items
                for item in doc_data.get('actionable_items', []):
                    await insert_actionable_item(conn, document_id, item)
        
        print(f"✅ Successfully loaded all data into database!")
        
        # Print summary
        total_clauses = sum(len(doc.get('key_clauses', [])) for doc in documents)
        total_metrics = sum(len(doc.get('key_metrics', [])) for doc in documents)
        total_actionable_items = sum(len(doc.get('actionable_items', [])) for doc in documents)
        
        print("\n📊 LOAD SUMMARY:")
        print(f"   Documents: {len(documents)}")
        print(f"   Key Clauses: {total_clauses}")
        print(f"   Key Metrics: {total_metrics}")
        print(f"   Actionable Items: {total_actionable_items}")
        
        return metadata_id
        
    finally:
        await conn.close()

async def insert_document(conn, metadata_id: str, doc_data: Dict[str, Any]) -> str:
    """Insert a single document"""
    document_id = str(uuid.uuid4())
    
    # Parse circular date
    circular_date = None
    original_metadata = doc_data.get('original_metadata', {})
    if original_metadata.get('circular_date'):
        try:
            date_str = original_metadata['circular_date']
            if ',' in date_str:
                circular_date = datetime.strptime(date_str, "%b %d, %Y").date()
            else:
                circular_date = datetime.strptime(date_str, "%b %d %Y").date()
        except:
            pass
    
    await conn.execute("""
        INSERT INTO sebi_documents (
            id, analysis_metadata_id, filename, title, department, summary, 
            content_length, intermediary, circular_number, circular_date, 
            source_url, link_text
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """, 
        document_id, metadata_id, doc_data.get('filename'), 
        doc_data.get('summary', '')[:500] if doc_data.get('summary') else None,
        doc_data.get('department'), doc_data.get('summary'), 
        doc_data.get('content_length'), doc_data.get('intermediary', []),
        original_metadata.get('circular_number'), circular_date,
        original_metadata.get('source_url'), original_metadata.get('link_text')
    )
    
    return document_id

async def insert_key_clause(conn, document_id: str, clause_data: Dict[str, Any]):
    """Insert a key clause"""
    clause_id = str(uuid.uuid4())
    
    # Parse effective date
    effective_date = None
    if clause_data.get('effective_date'):
        try:
            date_str = clause_data['effective_date']
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"]:
                try:
                    effective_date = datetime.strptime(date_str, fmt).date()
                    break
                except:
                    continue
        except:
            pass
    
    await conn.execute("""
        INSERT INTO sebi_key_clauses (
            id, document_id, clause_title, clause_content, regulatory_impact,
            compliance_level, effective_date, penalty_consequences
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        clause_id, document_id, clause_data.get('clause_title', ''),
        clause_data.get('clause_content', ''), clause_data.get('regulatory_impact'),
        map_compliance_level(clause_data.get('compliance_level', 'mandatory')), effective_date,
        clause_data.get('penalty_consequences')
    )

async def insert_key_metric(conn, document_id: str, metric_data: Dict[str, Any]):
    """Insert a key metric"""
    metric_id = str(uuid.uuid4())
    
    # Map metric types to valid enum values using the mapping function
    metric_type = map_metric_type(metric_data.get('metric_type', 'other'))
    
    await conn.execute("""
        INSERT INTO sebi_key_metrics (
            id, document_id, metric_type, metric_value, metric_description,
            applicable_entities, calculation_method, reporting_frequency, threshold_significance
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """,
        metric_id, document_id, metric_type,
        str(metric_data.get('metric_value', '')), metric_data.get('metric_description', ''),
        metric_data.get('applicable_entities'), metric_data.get('calculation_method'),
        metric_data.get('reporting_frequency'), metric_data.get('threshold_significance')
    )

async def insert_actionable_item(conn, document_id: str, item_data: Dict[str, Any]):
    """Insert an actionable item"""
    item_id = str(uuid.uuid4())
    
    await conn.execute("""
        INSERT INTO sebi_actionable_items (
            id, document_id, action_title, action_description, responsible_parties,
            implementation_timeline, compliance_requirements, documentation_needed,
            monitoring_mechanism, non_compliance_consequences
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """,
        item_id, document_id, item_data.get('action_title', ''),
        item_data.get('action_description'), item_data.get('responsible_parties'),
        item_data.get('implementation_timeline'), item_data.get('compliance_requirements'),
        item_data.get('documentation_needed'), item_data.get('monitoring_mechanism'),
        item_data.get('non_compliance_consequences')
    )

async def main():
    """Main function to load SEBI data"""
    print("🚀 SEBI Data Loader (Fixed Version)")
    print("=" * 50)
    
    # Path to the JSON file
    json_file_path = r"d:\langchain\LangGraph\output\sebi_document_analysis_results.json"
    
    try:
        metadata_id = await load_sebi_json_to_database(json_file_path)
        print(f"\n🎉 Success! Data loaded with metadata ID: {metadata_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
