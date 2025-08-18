"""
Simple script to create SEBI analysis tables manually
"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://neondb_owner:npg_2aZoeNujTmA5@ep-bold-dawn-adz91n9q.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

async def create_tables():
    """Create SEBI analysis tables"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Connected to database successfully!")
        
        # Create enums
        print("Creating enums...")
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE compliance_level AS ENUM ('mandatory', 'conditional', 'advisory', 'informational');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE metric_type AS ENUM ('timeline', 'amount', 'count', 'percentage', 'rate', 'other');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Main analysis results table
        print("Creating sebi_analysis_metadata table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sebi_analysis_metadata (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                total_files INTEGER NOT NULL,
                scrape_timestamp TIMESTAMP WITH TIME ZONE,
                analysis_timestamp TIMESTAMP WITH TIME ZONE,
                workflow_id VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Documents table for SEBI analysis
        print("Creating sebi_documents table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sebi_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                analysis_metadata_id UUID REFERENCES sebi_analysis_metadata(id),
                filename VARCHAR(255) NOT NULL,
                title TEXT,
                department VARCHAR(200),
                summary TEXT,
                content_length INTEGER,
                intermediary TEXT[], -- Array of intermediary types
                
                -- Original metadata
                circular_number VARCHAR(100),
                circular_date DATE,
                source_url TEXT,
                link_text TEXT,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Key clauses table
        print("Creating sebi_key_clauses table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sebi_key_clauses (
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
        
        # Key metrics table
        print("Creating sebi_key_metrics table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sebi_key_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES sebi_documents(id) ON DELETE CASCADE,
                metric_type metric_type NOT NULL,
                metric_value VARCHAR(100) NOT NULL,
                metric_description TEXT NOT NULL,
                applicable_entities TEXT,
                calculation_method TEXT,
                reporting_frequency VARCHAR(100),
                threshold_significance TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Actionable items table
        print("Creating sebi_actionable_items table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sebi_actionable_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES sebi_documents(id) ON DELETE CASCADE,
                action_title VARCHAR(500) NOT NULL,
                action_description TEXT,
                responsible_parties TEXT,
                implementation_timeline VARCHAR(200),
                compliance_requirements TEXT,
                documentation_needed TEXT,
                monitoring_mechanism TEXT,
                non_compliance_consequences TEXT,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes
        print("Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sebi_documents_dept ON sebi_documents(department);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_documents_circular_date ON sebi_documents(circular_date);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_documents_analysis_metadata ON sebi_documents(analysis_metadata_id);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_document ON sebi_key_clauses(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_compliance ON sebi_key_clauses(compliance_level);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_effective_date ON sebi_key_clauses(effective_date);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_key_metrics_document ON sebi_key_metrics(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_key_metrics_type ON sebi_key_metrics(metric_type);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_actionable_items_document ON sebi_actionable_items(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_sebi_actionable_items_completed ON sebi_actionable_items(is_completed);"
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print("✓ All SEBI analysis tables created successfully!")
        
        # Show table counts
        tables = ["sebi_analysis_metadata", "sebi_documents", "sebi_key_clauses", "sebi_key_metrics", "sebi_actionable_items"]
        print("\nTable counts:")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table};")
            print(f"  {table}: {count} rows")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
