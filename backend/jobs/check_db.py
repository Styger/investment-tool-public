"""
Check screening jobs database
Quick tool to inspect jobs in the queue
"""

import sqlite3
import json
from datetime import datetime


def check_database():
    """Display all jobs in the database"""
    db_path = "backend/jobs/screening_jobs.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count jobs by status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM screening_jobs 
            GROUP BY status
        """)

        print("=" * 60)
        print("📊 SCREENING JOBS DATABASE")
        print("=" * 60)
        print("\nJobs by Status:")

        status_counts = cursor.fetchall()
        if status_counts:
            for status, count in status_counts:
                print(f"  {status.upper()}: {count}")
        else:
            print("  No jobs found")

        # Show all jobs
        cursor.execute("""
            SELECT id, user_id, status, strategy_name, universe_name, 
                   created_at, progress, stocks_processed, stocks_total
            FROM screening_jobs 
            ORDER BY created_at DESC
            LIMIT 10
        """)

        print("\n" + "=" * 60)
        print("Recent Jobs (Latest 10):")
        print("=" * 60)

        jobs = cursor.fetchall()
        if jobs:
            for job in jobs:
                (
                    job_id,
                    user_id,
                    status,
                    strategy,
                    universe,
                    created,
                    progress,
                    processed,
                    total,
                ) = job

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(created)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = created[:19]

                # Status emoji
                status_emoji = {
                    "pending": "⏸️",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(status, "❓")

                print(f"\n{status_emoji} {status.upper()}")
                print(f"   ID: {job_id[:8]}...")
                print(f"   User: {user_id}")
                print(f"   Strategy: {strategy}")
                print(f"   Universe: {universe}")
                print(f"   Created: {time_str}")
                if processed and total:
                    print(f"   Progress: {processed}/{total} stocks ({progress}%)")
        else:
            print("\nNo jobs found in database")

        # Show latest completed job results
        cursor.execute("""
            SELECT id, strategy_name, result_summary
            FROM screening_jobs 
            WHERE status = 'completed' AND result_summary IS NOT NULL
            ORDER BY completed_at DESC
            LIMIT 1
        """)

        latest_result = cursor.fetchone()
        if latest_result:
            job_id, strategy, summary_json = latest_result
            summary = json.loads(summary_json)

            print("\n" + "=" * 60)
            print("Latest Completed Job Results:")
            print("=" * 60)
            print(f"Strategy: {strategy}")
            print(f"Total Stocks: {summary.get('total_stocks', 0)}")
            print(f"BUY: {summary.get('buy_count', 0)}")
            print(f"HOLD: {summary.get('hold_count', 0)}")
            print(f"SELL: {summary.get('sell_count', 0)}")
            print(f"Avg MOS: {summary.get('avg_mos', 0):.1f}%")
            print(f"Avg Moat: {summary.get('avg_moat', 0):.1f}")

        conn.close()
        print("\n" + "=" * 60)

    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
        print(f"💡 Database file: {db_path}")
        print("Make sure the database file exists!")
    except Exception as e:
        print(f"❌ Error: {e}")


def clear_all_jobs():
    """Clear all jobs from database (for testing)"""
    db_path = "backend/jobs/screening_jobs.db"

    response = input("⚠️  Delete ALL jobs from database? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Cancelled")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM screening_jobs")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✅ Deleted {deleted} jobs")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_all_jobs()
    else:
        check_database()
