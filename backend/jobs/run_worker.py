"""
Simple launcher script for the screening worker
Run this to start processing jobs
"""

from backend.jobs.screening_worker import ScreeningWorker
import signal
import sys


def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    print("\n⏹️  Worker stopping...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    print("=" * 60)
    print("  ValueKit Screening Worker")
    print("=" * 60)
    print()

    try:
        worker = ScreeningWorker(poll_interval=5)
        worker.start()
    except KeyboardInterrupt:
        print("\n⏹️  Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker crashed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
