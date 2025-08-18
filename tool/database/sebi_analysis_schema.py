"""
Database schema for SEBI Document Analysis Results
Comprehensive table structures to store all analyzed SEBI document data
"""

import asyncpg
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import uuid

from .index import DatabaseManager, DATABASE_URL


class SEBIAnalysisDBManager(DatabaseManager):
    """Extended database manager for SEBI analysis results"""
    
    async def create_sebi_analysis_tables(self):
        """Create tables specifically for SEBI analysis results"""
        conn = await self.get_async_connection()
        try:
            # Create enums for SEBI-specific data
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
                    assigned_team_id UUID REFERENCES teams(id), -- Link to existing teams table
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_documents_dept ON sebi_documents(department);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_documents_circular_date ON sebi_documents(circular_date);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_documents_analysis_metadata ON sebi_documents(analysis_metadata_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_document ON sebi_key_clauses(document_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_compliance ON sebi_key_clauses(compliance_level);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_key_clauses_effective_date ON sebi_key_clauses(effective_date);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_key_metrics_document ON sebi_key_metrics(document_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_key_metrics_type ON sebi_key_metrics(metric_type);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_actionable_items_document ON sebi_actionable_items(document_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_actionable_items_team ON sebi_actionable_items(assigned_team_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sebi_actionable_items_completed ON sebi_actionable_items(is_completed);")
            
            print("SEBI analysis tables created successfully!")
            
        finally:
            await conn.close()
    
    async def insert_sebi_analysis_data(self, analysis_data: Dict[str, Any]) -> str:
        """Insert complete SEBI analysis data from JSON"""
        conn = await self.get_async_connection()
        try:
            # Start transaction
            async with conn.transaction():
                # Insert metadata
                metadata = analysis_data.get('metadata', {})
                metadata_id = str(uuid.uuid4())
                
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
                
                # Insert documents and related data
                documents = analysis_data.get('documents', [])
                for doc_data in documents:
                    document_id = await self._insert_document(conn, metadata_id, doc_data)
                    
                    # Insert key clauses
                    for clause in doc_data.get('key_clauses', []):
                        await self._insert_key_clause(conn, document_id, clause)
                    
                    # Insert key metrics
                    for metric in doc_data.get('key_metrics', []):
                        await self._insert_key_metric(conn, document_id, metric)
                    
                    # Insert actionable items
                    for item in doc_data.get('actionable_items', []):
                        await self._insert_actionable_item(conn, document_id, item)
                
                return metadata_id
                
        finally:
            await conn.close()
    
    async def _insert_document(self, conn, metadata_id: str, doc_data: Dict[str, Any]) -> str:
        """Insert a single document"""
        document_id = str(uuid.uuid4())
        
        # Parse circular date
        circular_date = None
        original_metadata = doc_data.get('original_metadata', {})
        if original_metadata.get('circular_date'):
            try:
                # Try to parse various date formats
                date_str = original_metadata['circular_date']
                if ',' in date_str:
                    # Format like "Aug 12, 2025"
                    circular_date = datetime.strptime(date_str, "%b %d, %Y").date()
                else:
                    # Format like "Aug 12 2025"
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
            doc_data.get('summary', '')[:500] if doc_data.get('summary') else None,  # Use summary as title if no title
            doc_data.get('department'), doc_data.get('summary'), 
            doc_data.get('content_length'), doc_data.get('intermediary', []),
            original_metadata.get('circular_number'), circular_date,
            original_metadata.get('source_url'), original_metadata.get('link_text')
        )
        
        return document_id
    
    async def _insert_key_clause(self, conn, document_id: str, clause_data: Dict[str, Any]):
        """Insert a key clause"""
        clause_id = str(uuid.uuid4())
        
        # Parse effective date
        effective_date = None
        if clause_data.get('effective_date') and clause_data['effective_date'] != 'Not Specified':
            try:
                # Try to parse various date formats
                date_str = clause_data['effective_date']
                if ',' in date_str:
                    effective_date = datetime.strptime(date_str, "%B %d, %Y").date()
                elif 'immediate' in date_str.lower():
                    effective_date = datetime.now().date()
            except:
                pass
        
        # Map compliance level
        compliance_level = 'mandatory'  # default
        if clause_data.get('compliance_level'):
            level = clause_data['compliance_level'].lower()
            if level in ['mandatory', 'conditional', 'advisory', 'informational']:
                compliance_level = level
        
        await conn.execute("""
            INSERT INTO sebi_key_clauses (
                id, document_id, clause_title, clause_content, regulatory_impact,
                compliance_level, effective_date, penalty_consequences
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            clause_id, document_id, clause_data.get('clause_title', ''),
            clause_data.get('clause_content', ''), clause_data.get('regulatory_impact'),
            compliance_level, effective_date, clause_data.get('penalty_consequences')
        )
    
    async def _insert_key_metric(self, conn, document_id: str, metric_data: Dict[str, Any]):
        """Insert a key metric"""
        metric_id = str(uuid.uuid4())
        
        # Map metric type
        metric_type = 'other'  # default
        if metric_data.get('metric_type'):
            m_type = metric_data['metric_type'].lower()
            if m_type in ['timeline', 'amount', 'count', 'percentage', 'rate', 'other']:
                metric_type = m_type
        
        await conn.execute("""
            INSERT INTO sebi_key_metrics (
                id, document_id, metric_type, metric_value, metric_description,
                applicable_entities, calculation_method, reporting_frequency, threshold_significance
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            metric_id, document_id, metric_type, metric_data.get('metric_value', ''),
            metric_data.get('metric_description', ''), metric_data.get('applicable_entities'),
            metric_data.get('calculation_method'), metric_data.get('reporting_frequency'),
            metric_data.get('threshold_significance')
        )
    
    async def _insert_actionable_item(self, conn, document_id: str, item_data: Dict[str, Any]):
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
    
    # Query methods for SEBI analysis data
    async def get_documents_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get all documents from a specific department"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT d.*, COUNT(kc.id) as clause_count, COUNT(km.id) as metric_count, 
                       COUNT(ai.id) as actionable_count
                FROM sebi_documents d
                LEFT JOIN sebi_key_clauses kc ON d.id = kc.document_id
                LEFT JOIN sebi_key_metrics km ON d.id = km.document_id
                LEFT JOIN sebi_actionable_items ai ON d.id = ai.document_id
                WHERE d.department ILIKE $1
                GROUP BY d.id
                ORDER BY d.circular_date DESC NULLS LAST, d.created_at DESC;
            """
            rows = await conn.fetch(query, f"%{department}%")
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_documents_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get documents within a date range"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT d.*, COUNT(kc.id) as clause_count, COUNT(km.id) as metric_count, 
                       COUNT(ai.id) as actionable_count
                FROM sebi_documents d
                LEFT JOIN sebi_key_clauses kc ON d.id = kc.document_id
                LEFT JOIN sebi_key_metrics km ON d.id = km.document_id
                LEFT JOIN sebi_actionable_items ai ON d.id = ai.document_id
                WHERE d.circular_date BETWEEN $1 AND $2
                GROUP BY d.id
                ORDER BY d.circular_date DESC, d.created_at DESC;
            """
            rows = await conn.fetch(query, start_date, end_date)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_actionable_items_by_compliance_urgency(self) -> List[Dict[str, Any]]:
        """Get actionable items sorted by compliance urgency"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT ai.*, d.department, d.circular_date, d.filename,
                       CASE 
                           WHEN ai.implementation_timeline ILIKE '%immediate%' THEN 1
                           WHEN ai.implementation_timeline ILIKE '%30 days%' OR ai.implementation_timeline ILIKE '%1 month%' THEN 2
                           WHEN ai.implementation_timeline ILIKE '%60 days%' OR ai.implementation_timeline ILIKE '%2 month%' THEN 3
                           WHEN ai.implementation_timeline ILIKE '%90 days%' OR ai.implementation_timeline ILIKE '%3 month%' THEN 4
                           ELSE 5
                       END as urgency_score
                FROM sebi_actionable_items ai
                JOIN sebi_documents d ON ai.document_id = d.id
                WHERE ai.is_completed = FALSE
                ORDER BY urgency_score ASC, d.circular_date DESC;
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_compliance_summary(self) -> Dict[str, Any]:
        """Get comprehensive compliance summary"""
        conn = await self.get_async_connection()
        try:
            # Get document counts by department
            dept_query = """
                SELECT department, COUNT(*) as doc_count
                FROM sebi_documents
                WHERE department IS NOT NULL
                GROUP BY department
                ORDER BY doc_count DESC;
            """
            dept_rows = await conn.fetch(dept_query)
            
            # Get compliance level distribution
            compliance_query = """
                SELECT compliance_level, COUNT(*) as clause_count
                FROM sebi_key_clauses
                GROUP BY compliance_level
                ORDER BY clause_count DESC;
            """
            compliance_rows = await conn.fetch(compliance_query)
            
            # Get actionable items status
            actions_query = """
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN is_completed THEN 1 END) as completed_actions,
                    COUNT(CASE WHEN assigned_team_id IS NOT NULL THEN 1 END) as assigned_actions
                FROM sebi_actionable_items;
            """
            actions_row = await conn.fetchrow(actions_query)
            
            # Get recent documents (last 30 days)
            recent_query = """
                SELECT COUNT(*) as recent_documents
                FROM sebi_documents
                WHERE circular_date >= CURRENT_DATE - INTERVAL '30 days';
            """
            recent_row = await conn.fetchrow(recent_query)
            
            return {
                "departments": [dict(row) for row in dept_rows],
                "compliance_levels": [dict(row) for row in compliance_rows],
                "actionable_items": dict(actions_row) if actions_row else {},
                "recent_documents": recent_row['recent_documents'] if recent_row else 0,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        finally:
            await conn.close()
    
    async def search_documents(self, search_term: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced search across SEBI documents"""
        conn = await self.get_async_connection()
        try:
            base_query = """
                SELECT DISTINCT d.*, 
                       COUNT(kc.id) as clause_count, 
                       COUNT(km.id) as metric_count, 
                       COUNT(ai.id) as actionable_count
                FROM sebi_documents d
                LEFT JOIN sebi_key_clauses kc ON d.id = kc.document_id
                LEFT JOIN sebi_key_metrics km ON d.id = km.document_id
                LEFT JOIN sebi_actionable_items ai ON d.id = ai.document_id
                WHERE (
                    d.filename ILIKE $1 OR 
                    d.summary ILIKE $1 OR 
                    d.department ILIKE $1 OR
                    d.circular_number ILIKE $1 OR
                    EXISTS (
                        SELECT 1 FROM sebi_key_clauses sc 
                        WHERE sc.document_id = d.id AND 
                        (sc.clause_title ILIKE $1 OR sc.clause_content ILIKE $1)
                    ) OR
                    EXISTS (
                        SELECT 1 FROM sebi_actionable_items sa 
                        WHERE sa.document_id = d.id AND 
                        (sa.action_title ILIKE $1 OR sa.action_description ILIKE $1)
                    )
                )
            """
            
            params = [f"%{search_term}%"]
            where_clauses = []
            
            if filters:
                if filters.get('department'):
                    where_clauses.append(f"d.department ILIKE ${len(params) + 1}")
                    params.append(f"%{filters['department']}%")
                
                if filters.get('start_date'):
                    where_clauses.append(f"d.circular_date >= ${len(params) + 1}")
                    params.append(filters['start_date'])
                
                if filters.get('end_date'):
                    where_clauses.append(f"d.circular_date <= ${len(params) + 1}")
                    params.append(filters['end_date'])
            
            if where_clauses:
                base_query += " AND " + " AND ".join(where_clauses)
            
            base_query += """
                GROUP BY d.id
                ORDER BY d.circular_date DESC NULLS LAST, d.created_at DESC
                LIMIT 100;
            """
            
            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]
        finally:
            await conn.close()


# Global SEBI analysis database manager instance
sebi_db_manager = SEBIAnalysisDBManager()

__all__ = ['SEBIAnalysisDBManager', 'sebi_db_manager']
