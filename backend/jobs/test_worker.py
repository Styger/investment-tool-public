"""
Test script to submit a test job and verify worker processes it
"""

from backend.jobs.screening_queue import ScreeningJobQueue
import time


def test_submit_job():
    """Submit a test job"""
    queue = ScreeningJobQueue()

    # Test job parameters
    job_id = queue.submit_job(
        user_id="test_user",
        strategy_id="test-strategy-123",
        strategy_name="Test Strategy",
        universe_key="test_3",
        universe_name="Test Universe (3 stocks)",
        parameters={
            "mos_threshold": 10.0,
            "moat_threshold": 30.0,
            "sell_mos_threshold": -5.0,
            "sell_moat_threshold": 25.0,
            "use_mos": True,
            "use_pbt": True,
            "use_tencap": True,
        },
    )

    print(f"✅ Test job submitted: {job_id}")
    print(f"📊 Waiting for worker to process...")
    print(f"💡 Make sure worker is running: python backend/jobs/run_worker.py")

    # Poll for completion
    for i in range(60):  # Wait up to 60 seconds
        time.sleep(1)
        job = queue.get_job(job_id)

        status = job["status"]
        progress = job.get("progress", 0)

        print(f"   Status: {status} | Progress: {progress}%", end="\r")

        if status == "completed":
            print(f"\n✅ Job completed!")
            print(f"   Results: {job.get('result_summary')}")
            break
        elif status == "failed":
            print(f"\n❌ Job failed: {job.get('error_message')}")
            break
    else:
        print(f"\n⏰ Timeout waiting for job")


if __name__ == "__main__":
    test_submit_job()
