import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiosqlite

from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from storage.db import get_db_connection
from models.repository import Repository, RepositoryStatus, RepositoryUpdate
from core.security import encrypt_token, decrypt_token

# -------------------------------
# Scan Repository
# -------------------------------
class ScanRepository:
    """Repository for scan jobs"""

    async def create(self, scan_job: ScanJob) -> ScanJob:
        """Create a new scan job"""
        scan_job.id = scan_job.id or str(uuid.uuid4())
        scan_job.created_at = scan_job.created_at or datetime.utcnow()

        db = await get_db_connection()
        await db.execute("""
            INSERT INTO scans (id, filename, status, created_at)
            VALUES (?, ?, ?, ?)
        """, (scan_job.id, scan_job.filename, scan_job.status, scan_job.created_at.isoformat()))
        await db.commit()
        return scan_job

    async def get_by_id(self, scan_id: str) -> Optional[ScanJob]:
        """Get scan job by ID"""
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT id, filename, status, created_at, completed_at, findings_count, error
            FROM scans WHERE id = ?
        """, (scan_id,))
        row = await cursor.fetchone()
        if row:
            return ScanJob(
                id=row[0],
                filename=row[1],
                status=ScanStatus(row[2]),
                created_at=datetime.fromisoformat(row[3]),
                completed_at=datetime.fromisoformat(row[4]) if row[4] else None,
                findings_count=row[5],
                error=row[6]
            )
        return None

    async def update_status(self, scan_id: str, status: ScanStatus, error: Optional[str] = None):
        """Update scan job status"""
        db = await get_db_connection()
        await db.execute("UPDATE scans SET status = ?, error = ? WHERE id = ?", (status, error, scan_id))
        await db.commit()

    async def update_completion(self, scan_id: str, status: str, findings_count: int):
        """Update scan job completion"""
        db = await get_db_connection()
        await db.execute("""
            UPDATE scans
            SET status = ?, completed_at = ?, findings_count = ?
            WHERE id = ?
        """, (status, datetime.utcnow().isoformat(), findings_count, scan_id))
        await db.commit()


# -------------------------------
# Finding Repository
# -------------------------------
class FindingRepository:
    """Repository for findings"""

    async def create(self, finding: Finding) -> Finding:
        """Create a new finding"""
        finding.id = str(uuid.uuid4())
        finding.created_at = datetime.utcnow()

        db = await get_db_connection()
        await db.execute("""
            INSERT INTO findings 
            (id, job_id, file_path, line_number, secret_type, secret, 
             severity, rule_id, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding.id, finding.job_id, finding.file_path, finding.line_number,
            finding.secret_type, finding.secret, finding.severity, finding.rule_id,
            finding.confidence, finding.created_at.isoformat()
        ))
        await db.commit()
        return finding

    async def get_by_job_id(
        self, job_id: str, page: int = 1, size: int = 20,
        severity: Optional[str] = None, secret_type: Optional[str] = None
    ) -> List[Finding]:
        """Get paginated findings by job ID"""
        offset = (page - 1) * size
        query = "SELECT id, job_id, file_path, line_number, secret_type, secret, severity, rule_id, confidence, created_at FROM findings WHERE job_id = ?"
        params = [job_id]

        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if secret_type:
            query += " AND secret_type = ?"
            params.append(secret_type)

        query += " ORDER BY severity DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([size, offset])

        findings = []
        db = await get_db_connection()
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        for row in rows:
            findings.append(Finding(
                id=row[0], job_id=row[1], file_path=row[2], line_number=row[3],
                secret_type=row[4], secret=row[5], severity=row[6], rule_id=row[7],
                confidence=row[8], created_at=datetime.fromisoformat(row[9])
            ))
        return findings

    async def get_all_by_job_id(self, job_id: str) -> List[Finding]:
        """Get all findings by job ID"""
        return await self.get_by_job_id(job_id, page=1, size=10000)

    async def count_by_job_id(
        self, job_id: str, severity: Optional[str] = None, secret_type: Optional[str] = None
    ) -> int:
        """Count findings by job ID"""
        query = "SELECT COUNT(*) FROM findings WHERE job_id = ?"
        params = [job_id]
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if secret_type:
            query += " AND secret_type = ?"
            params.append(secret_type)

        db = await get_db_connection()
        cursor = await db.execute(query, params)
        result = await cursor.fetchone()
        return result[0] if result else 0

    async def get_statistics_by_job_id(self, job_id: str) -> Dict[str, Any]:
        """Get statistics for a scan job"""
        stats = {}
        db = await get_db_connection()
        
        # Total findings
        cursor = await db.execute("SELECT COUNT(*) FROM findings WHERE job_id = ?", (job_id,))
        result = await cursor.fetchone()
        stats["total"] = result[0] if result else 0

        # By severity
        cursor = await db.execute("""
            SELECT severity, COUNT(*) FROM findings WHERE job_id = ? GROUP BY severity
        """, (job_id,))
        rows = await cursor.fetchall()
        for severity, count in rows:
            stats[severity] = count

        # By type
        cursor = await db.execute("""
            SELECT secret_type, COUNT(*) FROM findings WHERE job_id = ? GROUP BY secret_type ORDER BY COUNT(*) DESC
        """, (job_id,))
        rows = await cursor.fetchall()
        stats["by_type"] = {secret_type: count for secret_type, count in rows}

        # Unique files scanned
        cursor = await db.execute("SELECT COUNT(DISTINCT file_path) FROM findings WHERE job_id = ?", (job_id,))
        result = await cursor.fetchone()
        stats["files_scanned"] = result[0] if result else 0

        return stats


# -------------------------------
# Repository Repository
# -------------------------------
class RepositoryRepository:
    """Repository for monitored repositories"""

    async def create(self, repository: Repository) -> Repository:
        """Create a new repository"""
        repository.id = repository.id or str(uuid.uuid4())
        repository.url = str(repository.url).rstrip("/")
        encrypted_token = encrypt_token(repository.token)

        db = await get_db_connection()
        await db.execute("""
            INSERT INTO repositories 
            (id, url, provider, name, token, status, webhook_secret, discord_webhook_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repository.id, repository.url, repository.provider, repository.name,
            encrypted_token, repository.status, repository.webhook_secret,
            str(repository.discord_webhook_url) if repository.discord_webhook_url else None,
            repository.created_at.isoformat()
        ))
        await db.commit()
        return repository

    async def get_by_id(self, repository_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT id, url, provider, name, token, status, webhook_secret,
                   discord_webhook_url, last_scan, last_scan_status, findings_count,
                   created_at, updated_at
            FROM repositories WHERE id = ?
        """, (repository_id,))
        row = await cursor.fetchone()
        if row:
            decrypted_token = decrypt_token(row[4])
            return Repository(
                id=row[0], url=row[1], provider=row[2], name=row[3], token=decrypted_token,
                status=row[5], webhook_secret=row[6],
                discord_webhook_url=row[7] if row[7] else None,
                last_scan=datetime.fromisoformat(row[8]) if row[8] else None,
                last_scan_status=row[9], findings_count=row[10],
                created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                updated_at=datetime.fromisoformat(row[12]) if row[12] else None
            )
        return None

    async def get_all(self) -> List[Repository]:
        """Get all repositories"""
        repositories = []
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT id, url, provider, name, token, status, webhook_secret,
                   discord_webhook_url, last_scan, last_scan_status, findings_count,
                   created_at, updated_at
            FROM repositories ORDER BY created_at DESC
        """)
        rows = await cursor.fetchall()
        for row in rows:
            decrypted_token = decrypt_token(row[4])
            repositories.append(Repository(
                id=row[0], url=row[1], provider=row[2], name=row[3], token=decrypted_token,
                status=row[5], webhook_secret=row[6],
                discord_webhook_url=row[7] if row[7] else None,
                last_scan=datetime.fromisoformat(row[8]) if row[8] else None,
                last_scan_status=row[9], findings_count=row[10],
                created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                updated_at=datetime.fromisoformat(row[12]) if row[12] else None
            ))
        return repositories

    async def get_active_repositories(self) -> List[Repository]:
        """Get all active repositories"""
        repositories = []
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT id, url, provider, name, token, status, webhook_secret,
                   discord_webhook_url, last_scan, last_scan_status, findings_count,
                   created_at, updated_at
            FROM repositories
            WHERE status = ? ORDER BY last_scan ASC NULLS FIRST
        """, ("active",))
        rows = await cursor.fetchall()
        for row in rows:
            decrypted_token = decrypt_token(row[4])
            repositories.append(Repository(
                id=row[0], url=row[1], provider=row[2], name=row[3], token=decrypted_token,
                status=RepositoryStatus(row[5]) if isinstance(row[5], str) else row[5], 
                webhook_secret=row[6],
                discord_webhook_url=row[7] if row[7] else None,
                last_scan=datetime.fromisoformat(row[8]) if row[8] else None,
                last_scan_status=row[9], findings_count=row[10],
                created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                updated_at=datetime.fromisoformat(row[12]) if row[12] else None
            ))
        return repositories

    async def update(self, repository_id: str, update_data: RepositoryUpdate) -> Repository:
        """Update repository"""
        update_fields = []
        params = []

        if update_data.name is not None:
            update_fields.append("name = ?")
            params.append(update_data.name)
        if update_data.token is not None:
            update_fields.append("token = ?")
            params.append(encrypt_token(update_data.token))
        if update_data.status is not None:
            update_fields.append("status = ?")
            params.append(update_data.status)
        if update_data.discord_webhook_url is not None:
            update_fields.append("discord_webhook_url = ?")
            params.append(str(update_data.discord_webhook_url))

        update_fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(repository_id)

        db = await get_db_connection()
        await db.execute(f"UPDATE repositories SET {', '.join(update_fields)} WHERE id = ?", params)
        await db.commit()
        return await self.get_by_id(repository_id)

    async def update_scan_status(
        self, repository_id: str, status: str, scan_time: datetime,
        findings_count: Optional[int] = None, error: Optional[str] = None
    ):
        """Update repository scan status"""
        db = await get_db_connection()
        if findings_count is not None:
            await db.execute("""
                UPDATE repositories
                SET last_scan = ?, last_scan_status = ?, findings_count = ?, updated_at = ?
                WHERE id = ?
            """, (scan_time.isoformat(), status, findings_count, datetime.utcnow().isoformat(), repository_id))
        else:
            await db.execute("""
                UPDATE repositories
                SET last_scan = ?, last_scan_status = ?, updated_at = ?
                WHERE id = ?
            """, (scan_time.isoformat(), status, datetime.utcnow().isoformat(), repository_id))
        await db.commit()

    async def delete(self, repository_id: str):
        """Delete repository"""
        db = await get_db_connection()
        await db.execute("DELETE FROM repositories WHERE id = ?", (repository_id,))
        await db.commit()


# -------------------------------
# Singleton instances
# -------------------------------
scan_repository = ScanRepository()
finding_repository = FindingRepository()
repository_repository = RepositoryRepository()