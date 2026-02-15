"""
Background Worker for Screening Jobs
Continuously processes pending screening jobs from the queue
"""

import time
import traceback
from datetime import datetime
from backend.jobs.screening_queue import ScreeningJobQueue
from backend.screening.screener import Screener
import pandas as pd


class ScreeningWorker:
    """Background worker that processes screening jobs"""

    def __init__(self, poll_interval: int = 5):
        """
        Initialize worker

        Args:
            poll_interval: Seconds between queue checks
        """
        self.queue = ScreeningJobQueue()
        self.poll_interval = poll_interval
        self.running = False

    def start(self):
        """Start the worker loop"""
        self.running = True
        print("🚀 Screening Worker started")
        print(f"📊 Polling every {self.poll_interval} seconds")
        print("Press Ctrl+C to stop\n")

        try:
            while self.running:
                self._process_next_job()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n⏹️  Worker stopped by user")
            self.running = False

    def stop(self):
        """Stop the worker"""
        self.running = False
        print("⏹️  Worker stopping...")

    def _process_next_job(self):
        """Process the next pending job in queue"""
        # Get next pending job
        job = self.queue.get_next_pending_job()

        if not job:
            # No pending jobs
            return

        job_id = job["id"]
        print(f"\n{'=' * 60}")
        print(f"🔄 Processing Job: {job_id}")
        print(f"   Strategy: {job['strategy_name']}")
        print(f"   Universe: {job['universe_name']}")
        print(f"   User: {job['user_id']}")
        print(f"{'=' * 60}")

        try:
            # Mark as running
            self.queue.update_job_status(job_id, "running", progress=0)
            print("✅ Job started")

            # Execute screening
            results_df = self._execute_screening(job)

            # Calculate summary
            summary = self._calculate_summary(results_df)

            # Save results
            results_json = results_df.to_json(orient="records")
            self.queue.save_job_results(job_id, results_json, summary)

            print(f"✅ Job completed successfully!")
            print(f"   Results: {len(results_df)} stocks screened")
            print(
                f"   BUY: {summary['buy_count']} | HOLD: {summary['hold_count']} | SELL: {summary['sell_count']}"
            )

        except Exception as e:
            # Handle errors
            error_msg = str(e)
            error_trace = traceback.format_exc()

            print(f"❌ Job failed: {error_msg}")
            print(f"\nTraceback:\n{error_trace}")

            self.queue.save_job_error(job_id, error_msg)

    def _execute_screening(self, job: dict) -> pd.DataFrame:
        """
        Execute the actual screening

        Args:
            job: Job configuration dict

        Returns:
            DataFrame with screening results
        """
        parameters = job["parameters"]
        universe_key = job["universe_key"]

        print(f"🔍 Screening {universe_key}...")

        # Run screening
        results_df = Screener.screen_market(
            strategy_params=parameters,
            universe_key=universe_key,
        )

        print(f"✅ Screening complete: {len(results_df)} stocks processed")

        return results_df

    def _calculate_summary(self, results_df: pd.DataFrame) -> dict:
        """Calculate summary statistics from results"""
        summary = {
            "total_stocks": len(results_df),
            "buy_count": len(results_df[results_df["Signal"] == "BUY"]),
            "hold_count": len(results_df[results_df["Signal"] == "HOLD"]),
            "sell_count": len(results_df[results_df["Signal"] == "SELL"]),
            "avg_mos": float(results_df["MOS %"].mean())
            if len(results_df) > 0
            else 0.0,
            "avg_moat": float(results_df["Moat Score"].mean())
            if len(results_df) > 0
            else 0.0,
        }

        return summary


def main():
    """Main entry point for worker"""
    worker = ScreeningWorker(poll_interval=5)
    worker.start()


if __name__ == "__main__":
    main()
