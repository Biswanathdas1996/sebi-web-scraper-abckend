"""
PostgreSQL Database Module for SEBI Document Analysis Workflow
Implements database operations for team assignments, document processing, and analysis results.
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import json

import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool


# Database connection configuration
DATABASE_URL = "postgresql://neondb_owner:npg_2aZoeNujTmA5@ep-bold-dawn-adz91n9q.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"


# Enum definitions matching TypeScript schema
class TeamType(str, Enum):
    LEGAL_COMPLIANCE = "legal_compliance"
    RISK_MANAGEMENT = "risk_management"
    OPERATIONS = "operations"
    FINANCE = "finance"
    EXECUTIVE = "executive"


class AssignmentStatus(str, Enum):
    AI_SUGGESTED = "ai_suggested"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REASSIGNED = "reassigned"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    INITIATED = "initiated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FinalStatus(str, Enum):
    SUCCESS = "SUCCESS"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


# Pydantic models for data validation
class TriggerWorkflowRequest(BaseModel):
    page_numbers: Optional[List[int]] = None
    download_folder: Optional[str] = None
    save_results: Optional[bool] = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    workflow_id: Optional[str] = None
    duration: Optional[str] = None
    final_status: Optional[FinalStatus] = None
    errors: Optional[List[str]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    page_numbers: Optional[List[int]] = None
    download_folder: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class ApiHealth(BaseModel):
    message: str
    version: str
    langsmith_enabled: bool
    timestamp: str


class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: TeamType
    description: Optional[str] = None
    color: str = "#3B82F6"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    title: Optional[str] = None
    summary: Optional[str] = None
    department: Optional[str] = None
    content_length: Optional[int] = None
    workflow_id: Optional[str] = None
    analysis_timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    team_id: str
    status: AssignmentStatus = AssignmentStatus.AI_SUGGESTED
    priority: PriorityLevel = PriorityLevel.MEDIUM
    assigned_by: Optional[str] = None
    ai_suggestion_reason: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActionableItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    title: str
    description: Optional[str] = None
    responsible_parties: Optional[str] = None
    implementation_timeline: Optional[str] = None
    compliance_requirements: Optional[str] = None
    documentation_needed: Optional[str] = None
    monitoring_mechanism: Optional[str] = None
    non_compliance_consequences: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    is_completed: bool = False
    created_at: Optional[datetime] = None


class ItemAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actionable_item_id: str
    team_id: str
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    assigned_by: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssignmentTimeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assignment_id: str
    action: str
    from_team_id: Optional[str] = None
    to_team_id: Optional[str] = None
    performed_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class DatabaseManager:
    """Main database manager class for PostgreSQL operations"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = create_engine(database_url, poolclass=NullPool)
    
    async def get_async_connection(self):
        """Get async database connection"""
        return await asyncpg.connect(self.database_url)
    
    def get_sync_connection(self):
        """Get synchronous database connection"""
        return psycopg2.connect(self.database_url)
    
    async def create_tables(self):
        """Create all database tables"""
        conn = await self.get_async_connection()
        try:
            # Create enums
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE team_type AS ENUM ('legal_compliance', 'risk_management', 'operations', 'finance', 'executive');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE assignment_status AS ENUM ('ai_suggested', 'assigned', 'in_progress', 'completed', 'reassigned', 'cancelled');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'critical');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            # Create tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL,
                    type team_type NOT NULL,
                    description TEXT,
                    color VARCHAR(7) DEFAULT '#3B82F6',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    filename VARCHAR(255) NOT NULL,
                    title VARCHAR(500),
                    summary TEXT,
                    department VARCHAR(100),
                    content_length INTEGER,
                    workflow_id VARCHAR(100),
                    analysis_timestamp TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_assignments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_id UUID REFERENCES documents(id) NOT NULL,
                    team_id UUID REFERENCES teams(id) NOT NULL,
                    status assignment_status DEFAULT 'ai_suggested',
                    priority priority_level DEFAULT 'medium',
                    assigned_by VARCHAR(100),
                    ai_suggestion_reason TEXT,
                    due_date TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS assignment_timeline (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    assignment_id UUID REFERENCES document_assignments(id) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    from_team_id UUID REFERENCES teams(id),
                    to_team_id UUID REFERENCES teams(id),
                    performed_by VARCHAR(100),
                    reason TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS actionable_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_id UUID REFERENCES documents(id) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    responsible_parties TEXT,
                    implementation_timeline VARCHAR(200),
                    compliance_requirements TEXT,
                    documentation_needed TEXT,
                    monitoring_mechanism TEXT,
                    non_compliance_consequences TEXT,
                    priority priority_level DEFAULT 'medium',
                    is_completed BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS item_assignments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    actionable_item_id UUID REFERENCES actionable_items(id) NOT NULL,
                    team_id UUID REFERENCES teams(id) NOT NULL,
                    status assignment_status DEFAULT 'assigned',
                    assigned_by VARCHAR(100),
                    due_date TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_assignment_timeline_assignment ON assignment_timeline(assignment_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_assignment_timeline_created ON assignment_timeline(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_workflow ON documents(workflow_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_document_assignments_status ON document_assignments(status);")
            
        finally:
            await conn.close()
    
    # Team operations
    async def create_team(self, team_data: Dict[str, Any]) -> str:
        """Create a new team"""
        conn = await self.get_async_connection()
        try:
            team = Team(**team_data)
            query = """
                INSERT INTO teams (id, name, type, description, color, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, team.id, team.name, team.type.value, 
                team.description, team.color, team.is_active
            )
            return result
        finally:
            await conn.close()
    
    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        conn = await self.get_async_connection()
        try:
            query = "SELECT * FROM teams WHERE id = $1;"
            row = await conn.fetchrow(query, team_id)
            return dict(row) if row else None
        finally:
            await conn.close()
    
    async def get_all_teams(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all teams"""
        conn = await self.get_async_connection()
        try:
            if active_only:
                query = "SELECT * FROM teams WHERE is_active = true ORDER BY name;"
            else:
                query = "SELECT * FROM teams ORDER BY name;"
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def update_team(self, team_id: str, update_data: Dict[str, Any]) -> bool:
        """Update team"""
        conn = await self.get_async_connection()
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            for key, value in update_data.items():
                if key not in ['id', 'created_at']:
                    set_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            if not set_clauses:
                return False
            
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.now(timezone.utc))
            values.append(team_id)
            
            query = f"""
                UPDATE teams 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count + 1};
            """
            
            result = await conn.execute(query, *values)
            return result == "UPDATE 1"
        finally:
            await conn.close()
    
    async def delete_team(self, team_id: str) -> bool:
        """Soft delete team by setting is_active to false"""
        return await self.update_team(team_id, {"is_active": False})
    
    # Document operations
    async def create_document(self, document_data: Dict[str, Any]) -> str:
        """Create a new document"""
        conn = await self.get_async_connection()
        try:
            doc = Document(**document_data)
            # Ensure timezone-aware datetime
            analysis_timestamp = doc.analysis_timestamp
            if analysis_timestamp and analysis_timestamp.tzinfo is None:
                analysis_timestamp = analysis_timestamp.replace(tzinfo=timezone.utc)
            
            query = """
                INSERT INTO documents (id, filename, title, summary, department, 
                                     content_length, workflow_id, analysis_timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, doc.id, doc.filename, doc.title, doc.summary,
                doc.department, doc.content_length, doc.workflow_id, 
                analysis_timestamp
            )
            return result
        finally:
            await conn.close()
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        conn = await self.get_async_connection()
        try:
            query = "SELECT * FROM documents WHERE id = $1;"
            row = await conn.fetchrow(query, document_id)
            return dict(row) if row else None
        finally:
            await conn.close()
    
    async def get_documents_by_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a workflow"""
        conn = await self.get_async_connection()
        try:
            query = "SELECT * FROM documents WHERE workflow_id = $1 ORDER BY created_at;"
            rows = await conn.fetch(query, workflow_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def search_documents(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents by filename, title, or summary"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT * FROM documents 
                WHERE filename ILIKE $1 OR title ILIKE $1 OR summary ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2;
            """
            search_pattern = f"%{search_term}%"
            rows = await conn.fetch(query, search_pattern, limit)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    # Document assignment operations
    async def create_document_assignment(self, assignment_data: Dict[str, Any]) -> str:
        """Create a new document assignment"""
        conn = await self.get_async_connection()
        try:
            assignment = DocumentAssignment(**assignment_data)
            # Ensure timezone-aware datetime
            due_date = assignment.due_date
            if due_date and due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            
            query = """
                INSERT INTO document_assignments (id, document_id, team_id, status, priority,
                                                assigned_by, ai_suggestion_reason, due_date, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, assignment.id, assignment.document_id, assignment.team_id,
                assignment.status.value, assignment.priority.value, assignment.assigned_by,
                assignment.ai_suggestion_reason, due_date, assignment.notes
            )
            
            # Log to timeline
            await self.log_assignment_timeline(
                assignment.id, "created", None, assignment.team_id,
                assignment.assigned_by, "Assignment created"
            )
            
            return result
        finally:
            await conn.close()
    
    async def get_document_assignments(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a document"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT da.*, t.name as team_name, t.type as team_type, t.color as team_color,
                       d.filename, d.title as document_title
                FROM document_assignments da
                JOIN teams t ON da.team_id = t.id
                JOIN documents d ON da.document_id = d.id
                WHERE da.document_id = $1
                ORDER BY da.created_at;
            """
            rows = await conn.fetch(query, document_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_team_assignments(self, team_id: str, status: Optional[AssignmentStatus] = None) -> List[Dict[str, Any]]:
        """Get all assignments for a team"""
        conn = await self.get_async_connection()
        try:
            if status:
                query = """
                    SELECT da.*, d.filename, d.title as document_title, d.summary
                    FROM document_assignments da
                    JOIN documents d ON da.document_id = d.id
                    WHERE da.team_id = $1 AND da.status = $2
                    ORDER BY da.priority DESC, da.due_date ASC NULLS LAST;
                """
                rows = await conn.fetch(query, team_id, status.value)
            else:
                query = """
                    SELECT da.*, d.filename, d.title as document_title, d.summary
                    FROM document_assignments da
                    JOIN documents d ON da.document_id = d.id
                    WHERE da.team_id = $1
                    ORDER BY da.priority DESC, da.due_date ASC NULLS LAST;
                """
                rows = await conn.fetch(query, team_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def update_assignment_status(self, assignment_id: str, status: AssignmentStatus, 
                                     updated_by: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Update assignment status"""
        conn = await self.get_async_connection()
        try:
            # Get current assignment
            current = await conn.fetchrow("SELECT * FROM document_assignments WHERE id = $1", assignment_id)
            if not current:
                return False
            
            # Update status
            update_data = {"status": status.value, "updated_at": datetime.now(timezone.utc)}
            if notes:
                update_data["notes"] = notes
            if status == AssignmentStatus.COMPLETED:
                update_data["completed_at"] = datetime.now(timezone.utc)
            
            query = """
                UPDATE document_assignments 
                SET status = $1, updated_at = $2, notes = COALESCE($3, notes),
                    completed_at = CASE WHEN $1 = 'completed' THEN $2 ELSE completed_at END
                WHERE id = $4;
            """
            result = await conn.execute(query, status.value, update_data["updated_at"], notes, assignment_id)
            
            # Log to timeline
            await self.log_assignment_timeline(
                assignment_id, f"status_changed_to_{status.value}", 
                current["team_id"], current["team_id"], updated_by, 
                f"Status changed to {status.value}"
            )
            
            return result == "UPDATE 1"
        finally:
            await conn.close()
    
    async def reassign_document(self, assignment_id: str, new_team_id: str, 
                              reassigned_by: Optional[str] = None, reason: Optional[str] = None) -> bool:
        """Reassign document to different team"""
        conn = await self.get_async_connection()
        try:
            # Get current assignment
            current = await conn.fetchrow("SELECT * FROM document_assignments WHERE id = $1", assignment_id)
            if not current:
                return False
            
            old_team_id = current["team_id"]
            
            # Update assignment
            query = """
                UPDATE document_assignments 
                SET team_id = $1, status = 'reassigned', updated_at = $2
                WHERE id = $3;
            """
            result = await conn.execute(query, new_team_id, datetime.now(timezone.utc), assignment_id)
            
            # Log to timeline
            await self.log_assignment_timeline(
                assignment_id, "reassigned", old_team_id, new_team_id, 
                reassigned_by, reason or "Document reassigned"
            )
            
            return result == "UPDATE 1"
        finally:
            await conn.close()
    
    # Timeline operations
    async def log_assignment_timeline(self, assignment_id: str, action: str, 
                                    from_team_id: Optional[str] = None, 
                                    to_team_id: Optional[str] = None,
                                    performed_by: Optional[str] = None, 
                                    reason: Optional[str] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log assignment timeline event"""
        conn = await self.get_async_connection()
        try:
            timeline = AssignmentTimeline(
                assignment_id=assignment_id,
                action=action,
                from_team_id=from_team_id,
                to_team_id=to_team_id,
                performed_by=performed_by,
                reason=reason,
                metadata=metadata
            )
            
            query = """
                INSERT INTO assignment_timeline (id, assignment_id, action, from_team_id, 
                                               to_team_id, performed_by, reason, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, timeline.id, timeline.assignment_id, timeline.action,
                timeline.from_team_id, timeline.to_team_id, timeline.performed_by,
                timeline.reason, json.dumps(timeline.metadata) if timeline.metadata else None
            )
            return result
        finally:
            await conn.close()
    
    async def get_assignment_timeline(self, assignment_id: str) -> List[Dict[str, Any]]:
        """Get timeline for assignment"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT at.*, 
                       ft.name as from_team_name, ft.type as from_team_type,
                       tt.name as to_team_name, tt.type as to_team_type
                FROM assignment_timeline at
                LEFT JOIN teams ft ON at.from_team_id = ft.id
                LEFT JOIN teams tt ON at.to_team_id = tt.id
                WHERE at.assignment_id = $1
                ORDER BY at.created_at;
            """
            rows = await conn.fetch(query, assignment_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    # Actionable items operations
    async def create_actionable_item(self, item_data: Dict[str, Any]) -> str:
        """Create actionable item"""
        conn = await self.get_async_connection()
        try:
            item = ActionableItem(**item_data)
            query = """
                INSERT INTO actionable_items (id, document_id, title, description, 
                                            responsible_parties, implementation_timeline,
                                            compliance_requirements, documentation_needed,
                                            monitoring_mechanism, non_compliance_consequences,
                                            priority, is_completed)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, item.id, item.document_id, item.title, item.description,
                item.responsible_parties, item.implementation_timeline,
                item.compliance_requirements, item.documentation_needed,
                item.monitoring_mechanism, item.non_compliance_consequences,
                item.priority.value, item.is_completed
            )
            return result
        finally:
            await conn.close()
    
    async def get_actionable_items_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get actionable items for document"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT ai.*, d.filename, d.title as document_title
                FROM actionable_items ai
                JOIN documents d ON ai.document_id = d.id
                WHERE ai.document_id = $1
                ORDER BY ai.priority DESC, ai.created_at;
            """
            rows = await conn.fetch(query, document_id)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def assign_actionable_item(self, item_id: str, team_id: str, 
                                   assigned_by: Optional[str] = None,
                                   due_date: Optional[datetime] = None,
                                   notes: Optional[str] = None) -> str:
        """Assign actionable item to team"""
        conn = await self.get_async_connection()
        try:
            # Ensure timezone-aware datetime
            if due_date and due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            
            assignment = ItemAssignment(
                actionable_item_id=item_id,
                team_id=team_id,
                assigned_by=assigned_by,
                due_date=due_date,
                notes=notes
            )
            
            query = """
                INSERT INTO item_assignments (id, actionable_item_id, team_id, status,
                                            assigned_by, due_date, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id;
            """
            result = await conn.fetchval(
                query, assignment.id, assignment.actionable_item_id, assignment.team_id,
                assignment.status.value, assignment.assigned_by, assignment.due_date,
                assignment.notes
            )
            return result
        finally:
            await conn.close()
    
    # Analytics and reporting
    async def get_team_workload_summary(self) -> List[Dict[str, Any]]:
        """Get workload summary for all teams"""
        conn = await self.get_async_connection()
        try:
            query = """
                SELECT t.id, t.name, t.type, t.color,
                       COUNT(da.id) as total_assignments,
                       COUNT(CASE WHEN da.status = 'ai_suggested' THEN 1 END) as ai_suggested,
                       COUNT(CASE WHEN da.status = 'assigned' THEN 1 END) as assigned,
                       COUNT(CASE WHEN da.status = 'in_progress' THEN 1 END) as in_progress,
                       COUNT(CASE WHEN da.status = 'completed' THEN 1 END) as completed,
                       COUNT(CASE WHEN da.priority = 'critical' THEN 1 END) as critical_items,
                       COUNT(CASE WHEN da.priority = 'high' THEN 1 END) as high_priority_items
                FROM teams t
                LEFT JOIN document_assignments da ON t.id = da.team_id
                WHERE t.is_active = true
                GROUP BY t.id, t.name, t.type, t.color
                ORDER BY t.name;
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    async def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a workflow"""
        conn = await self.get_async_connection()
        try:
            # Get workflow documents
            documents = await self.get_documents_by_workflow(workflow_id)
            
            # Get assignment statistics
            stats_query = """
                SELECT da.status, da.priority, COUNT(*) as count
                FROM document_assignments da
                JOIN documents d ON da.document_id = d.id
                WHERE d.workflow_id = $1
                GROUP BY da.status, da.priority;
            """
            stats_rows = await conn.fetch(stats_query, workflow_id)
            
            # Get team distribution
            team_query = """
                SELECT t.name, t.type, COUNT(da.id) as assignments
                FROM teams t
                JOIN document_assignments da ON t.id = da.team_id
                JOIN documents d ON da.document_id = d.id
                WHERE d.workflow_id = $1
                GROUP BY t.id, t.name, t.type
                ORDER BY assignments DESC;
            """
            team_rows = await conn.fetch(team_query, workflow_id)
            
            return {
                "workflow_id": workflow_id,
                "total_documents": len(documents),
                "documents": documents,
                "assignment_statistics": [dict(row) for row in stats_rows],
                "team_distribution": [dict(row) for row in team_rows],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        finally:
            await conn.close()
    
    # Utility functions
    async def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            conn = await self.get_async_connection()
            try:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1;")
                
                # Get table counts
                tables = ["teams", "documents", "document_assignments", "actionable_items"]
                table_counts = {}
                for table in tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table};")
                    table_counts[table] = count
                
                return {
                    "status": "healthy",
                    "connection": "ok",
                    "test_query": result == 1,
                    "table_counts": table_counts,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            finally:
                await conn.close()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup_old_records(self, days_old: int = 90) -> Dict[str, int]:
        """Cleanup old records (soft delete)"""
        conn = await self.get_async_connection()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Archive old completed assignments
            completed_query = """
                UPDATE document_assignments 
                SET notes = CONCAT('ARCHIVED: ', COALESCE(notes, ''))
                WHERE status = 'completed' 
                AND completed_at < $1 
                AND notes NOT LIKE 'ARCHIVED:%';
            """
            completed_result = await conn.execute(completed_query, cutoff_date)
            
            return {
                "archived_assignments": int(completed_result.split()[-1]) if completed_result else 0,
                "cutoff_date": cutoff_date.isoformat()
            }
        finally:
            await conn.close()


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for common operations
async def initialize_database():
    """Initialize database with tables and default teams"""
    await db_manager.create_tables()
    
    # Create default teams if they don't exist
    default_teams = [
        {
            "name": "Legal & Compliance",
            "type": TeamType.LEGAL_COMPLIANCE,
            "description": "Handles legal matters, regulatory compliance, and policy interpretation",
            "color": "#DC2626"
        },
        {
            "name": "Risk Management",
            "type": TeamType.RISK_MANAGEMENT,
            "description": "Manages operational and strategic risks",
            "color": "#D97706"
        },
        {
            "name": "Operations",
            "type": TeamType.OPERATIONS,
            "description": "Handles day-to-day operational activities and implementations",
            "color": "#059669"
        },
        {
            "name": "Finance",
            "type": TeamType.FINANCE,
            "description": "Manages financial compliance and reporting requirements",
            "color": "#7C3AED"
        },
        {
            "name": "Executive",
            "type": TeamType.EXECUTIVE,
            "description": "Executive oversight and strategic decisions",
            "color": "#BE185D"
        }
    ]
    
    existing_teams = await db_manager.get_all_teams()
    if not existing_teams:
        for team_data in default_teams:
            await db_manager.create_team(team_data)


# Export main functions and classes
__all__ = [
    'DatabaseManager', 'db_manager', 'initialize_database',
    'Team', 'Document', 'DocumentAssignment', 'ActionableItem', 'ItemAssignment',
    'TeamType', 'AssignmentStatus', 'PriorityLevel', 'TaskStatus', 'FinalStatus',
    'TriggerWorkflowRequest', 'TaskStatusResponse', 'ApiHealth'
]

# Import SEBI analysis schema if available
try:
    from .sebi_analysis_schema import sebi_db_manager, SEBIAnalysisDBManager
    __all__.extend(['sebi_db_manager', 'SEBIAnalysisDBManager'])
except ImportError:
    pass