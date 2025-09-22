import sqlite3
import aiosqlite
import os
from datetime import datetime

DATABASE_FILE = "secrethawk.db"

async def init_db():
    """Initialize the database with required tables"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        # Create scans table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                findings_count INTEGER,
                error TEXT
            )
        """)
        
        # Create findings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                secret_type TEXT NOT NULL,
                secret TEXT NOT NULL,
                severity TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES scans (id)
            )
        """)
        
        # Create indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_findings_job_id ON findings(job_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)")
        
        # Create repositories table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                provider TEXT NOT NULL,
                name TEXT NOT NULL,
                token TEXT NOT NULL,
                status TEXT NOT NULL,
                webhook_secret TEXT,
                discord_webhook_url TEXT,
                last_scan TEXT,
                last_scan_status TEXT,
                findings_count INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Create indexes for repositories
        await db.execute("CREATE INDEX IF NOT EXISTS idx_repositories_status ON repositories(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_repositories_last_scan ON repositories(last_scan)")
        
        await db.commit()

async def get_db_connection():
    """Get database connection"""
    return await aiosqlite.connect(DATABASE_FILE)