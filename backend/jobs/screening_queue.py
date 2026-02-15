"""
Screening Job Queue Manager
Handles async screening job submission, status tracking, and result storage
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ScreeningJobQueue:
    """Manage screening jobs in SQLite queue"""

    def __init__(self, db_path: str = "backend/jobs/screening_jobs.db"):
        """Initialize job queue"""
        self.db_path = db_path

        # Create directory if not exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                
                strategy_id TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                universe_key TEXT NOT NULL,
                universe_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                
                results TEXT,
                error_message TEXT,
                
                progress INTEGER DEFAULT 0,
                stocks_processed INTEGER DEFAULT 0,
                stocks_total INTEGER DEFAULT 0,
                
                result_summary TEXT
            )
        """)

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_screening_user_status ON screening_jobs(user_id, status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_screening_created ON screening_jobs(created_at DESC)"
        )

        conn.commit()
        conn.close()

    def submit_job(
        self,
        user_id: str,
        strategy_id: str,
        strategy_name: str,
        universe_key: str,
        universe_name: str,
        parameters: Dict,
    ) -> str:
        """
        Submit a new screening job

        Returns:
            job_id: Unique job identifier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        job_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO screening_jobs 
            (id, user_id, status, created_at, strategy_id, strategy_name, 
             universe_key, universe_name, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                user_id,
                "pending",
                timestamp,
                strategy_id,
                strategy_name,
                universe_key,
                universe_name,
                json.dumps(parameters),
            ),
        )

        conn.commit()
        conn.close()

        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM screening_jobs WHERE id = ?", (job_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()

        if row:
            job = dict(zip(columns, row))
            job["parameters"] = (
                json.loads(job["parameters"]) if job["parameters"] else {}
            )
            if job.get("results"):
                job["results"] = json.loads(job["results"])
            if job.get("result_summary"):
                job["result_summary"] = json.loads(job["result_summary"])
            conn.close()
            return job

        conn.close()
        return None

    def get_user_jobs(
        self, user_id: str, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """Get all jobs for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT * FROM screening_jobs 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, status, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM screening_jobs 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )

        columns = [description[0] for description in cursor.description]
        jobs = []

        for row in cursor.fetchall():
            job = dict(zip(columns, row))
            job["parameters"] = (
                json.loads(job["parameters"]) if job["parameters"] else {}
            )
            if job.get("results"):
                job["results"] = json.loads(job["results"])
            if job.get("result_summary"):
                job["result_summary"] = json.loads(job["result_summary"])
            jobs.append(job)

        conn.close()
        return jobs

    def get_next_pending_job(self) -> Optional[Dict]:
        """Get next pending job (FIFO)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM screening_jobs 
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            """
        )

        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()

        if row:
            job = dict(zip(columns, row))
            job["parameters"] = (
                json.loads(job["parameters"]) if job["parameters"] else {}
            )
            conn.close()
            return job

        conn.close()
        return None

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int = None,
        stocks_processed: int = None,
        stocks_total: int = None,
    ):
        """Update job status and progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = ["status = ?"]
        values = [status]

        if status == "running" and not self.get_job(job_id).get("started_at"):
            updates.append("started_at = ?")
            values.append(datetime.now().isoformat())

        if status in ["completed", "failed", "cancelled"]:
            updates.append("completed_at = ?")
            values.append(datetime.now().isoformat())

        if progress is not None:
            updates.append("progress = ?")
            values.append(progress)

        if stocks_processed is not None:
            updates.append("stocks_processed = ?")
            values.append(stocks_processed)

        if stocks_total is not None:
            updates.append("stocks_total = ?")
            values.append(stocks_total)

        values.append(job_id)

        cursor.execute(
            f"UPDATE screening_jobs SET {', '.join(updates)} WHERE id = ?", values
        )

        conn.commit()
        conn.close()

    def save_job_results(self, job_id: str, results_df_json: str, summary: Dict):
        """Save screening results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE screening_jobs 
            SET results = ?, result_summary = ?, status = 'completed', completed_at = ?
            WHERE id = ?
            """,
            (results_df_json, json.dumps(summary), datetime.now().isoformat(), job_id),
        )

        conn.commit()
        conn.close()

    def save_job_error(self, job_id: str, error_message: str):
        """Save job error"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE screening_jobs 
            SET status = 'failed', error_message = ?, completed_at = ?
            WHERE id = ?
            """,
            (error_message, datetime.now().isoformat(), job_id),
        )

        conn.commit()
        conn.close()

    def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Cancel a pending job (only if owned by user)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE screening_jobs 
            SET status = 'cancelled', completed_at = ?
            WHERE id = ? AND user_id = ? AND status = 'pending'
            """,
            (datetime.now().isoformat(), job_id, user_id),
        )

        cancelled = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return cancelled

    def delete_job(self, job_id: str, user_id: str) -> bool:
        """Delete a job (only if owned by user)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM screening_jobs WHERE id = ? AND user_id = ?", (job_id, user_id)
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted
