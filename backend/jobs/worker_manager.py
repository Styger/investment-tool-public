"""
Worker Manager - Auto-start and manage background worker
Handles both subprocess worker and fallback polling
"""

import subprocess
import threading
import time
import os
import sys
from pathlib import Path


class WorkerManager:
    """Manage background worker process"""

    _instance = None
    _worker_process = None
    _polling_thread = None
    _polling_active = False

    def __new__(cls):
        """Singleton pattern - only one manager instance"""
        if cls._instance is None:
            cls._instance = super(WorkerManager, cls).__new__(cls)
        return cls._instance

    def start_worker(self, mode="auto"):
        """
        Start the background worker

        Args:
            mode: "subprocess", "polling", or "auto" (try subprocess, fallback to polling)
        """
        if mode == "auto":
            # Try subprocess first
            if self._start_subprocess_worker():
                print("✅ Worker started as subprocess")
                return True
            else:
                # Fallback to polling
                print("⚠️ Subprocess worker failed, using polling mode")
                self._start_polling_worker()
                return True
        elif mode == "subprocess":
            return self._start_subprocess_worker()
        elif mode == "polling":
            self._start_polling_worker()
            return True

        return False

    def _start_subprocess_worker(self):
        """Start worker as separate subprocess"""
        if self._worker_process is not None:
            # Worker already running
            if self._worker_process.poll() is None:
                return True
            else:
                # Process died, clean up
                self._worker_process = None

        try:
            # Get path to worker script
            worker_script = Path(__file__).parent / "run_worker.py"

            # Start worker process with proper flags
            self._worker_process = subprocess.Popen(
                [sys.executable, "-m", "backend.jobs.run_worker"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,  # Don't read stdin
                # Add these flags for better subprocess handling
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32"
                else 0,
            )

            # Wait to see if it crashes immediately
            time.sleep(1.0)  # Increased from 0.5

            # Check if process is still running
            poll_result = self._worker_process.poll()
            if poll_result is None:
                print(f"✅ Subprocess worker started (PID: {self._worker_process.pid})")
                return True
            else:
                # Process died - get error output
                stdout, stderr = self._worker_process.communicate(timeout=1)
                print(f"❌ Subprocess died with code {poll_result}")
                if stderr:
                    print(f"   Error: {stderr.decode()[:500]}")
                self._worker_process = None
                return False

        except Exception as e:
            print(f"❌ Failed to start subprocess worker: {e}")
            import traceback

            traceback.print_exc()
            self._worker_process = None
            return False

    def _start_polling_worker(self):
        """Start worker as background thread with polling"""
        if self._polling_thread is not None and self._polling_thread.is_alive():
            # Already running
            return

        self._polling_active = True
        self._polling_thread = threading.Thread(
            target=self._polling_worker_loop,
            daemon=True,  # Thread dies when main program exits
        )
        self._polling_thread.start()

    def _polling_worker_loop(self):
        """Background thread that processes jobs"""
        from backend.jobs.screening_worker import ScreeningWorker

        worker = ScreeningWorker(poll_interval=5)

        print("🔄 Polling worker started (background thread)")

        while self._polling_active:
            try:
                # Process one job
                worker._process_next_job()
                time.sleep(5)
            except Exception as e:
                print(f"❌ Polling worker error: {e}")
                time.sleep(5)

    def stop_worker(self):
        """Stop the worker (subprocess or polling)"""
        # Stop subprocess
        if self._worker_process is not None:
            self._worker_process.terminate()
            self._worker_process.wait(timeout=5)
            self._worker_process = None
            print("⏹️ Subprocess worker stopped")

        # Stop polling thread
        if self._polling_thread is not None:
            self._polling_active = False
            self._polling_thread.join(timeout=5)
            self._polling_thread = None
            print("⏹️ Polling worker stopped")

    def is_running(self):
        """Check if worker is running"""
        # Check subprocess
        if self._worker_process is not None and self._worker_process.poll() is None:
            return True

        # Check polling thread
        if self._polling_thread is not None and self._polling_thread.is_alive():
            return True

        return False

    def get_status(self):
        """Get worker status"""
        if self._worker_process is not None and self._worker_process.poll() is None:
            return "subprocess"
        elif self._polling_thread is not None and self._polling_thread.is_alive():
            return "polling"
        else:
            return "stopped"


# Global worker manager instance
_worker_manager = None


def get_worker_manager():
    """Get or create global worker manager"""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager()
    return _worker_manager


def ensure_worker_running():
    """Ensure worker is running (auto-start if needed)"""
    manager = get_worker_manager()

    if not manager.is_running():
        print("🚀 Starting background worker...")
        manager.start_worker(mode="auto")

    return manager
