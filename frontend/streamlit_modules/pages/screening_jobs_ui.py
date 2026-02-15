"""
Screening Jobs Management Page
View and manage screening jobs
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time


def show_screening_jobs_page():
    """Display user's screening jobs"""

    # Page config
    st.set_page_config(
        page_title="My Screening Jobs - ValueKit",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 My Screening Jobs")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Back button
        if st.button("← Back to Screening"):
            st.session_state["current_page"] = "screening"
            st.rerun()

    with col2:
        # MANUAL PROCESS BUTTON
        if st.button("🔄 Process Jobs Now", help="Manually process pending jobs"):
            try:
                from backend.jobs.screening_worker import ScreeningWorker

                worker = ScreeningWorker(poll_interval=0)

                # Process one job
                worker._process_next_job()

                st.success("✅ Processed pending job!")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.divider()

    try:
        from backend.jobs.screening_queue import ScreeningJobQueue

        queue = ScreeningJobQueue()
        current_user = st.session_state.get("username", "default_user")

        # Auto-refresh toggle
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Active & Recent Jobs")

        with col2:
            auto_refresh = st.checkbox(
                "🔄 Auto-Refresh", value=True, help="Refresh every 10 seconds"
            )

        # Get user jobs
        jobs = queue.get_user_jobs(current_user, limit=50)

        if not jobs:
            st.info("📭 No screening jobs yet. Go back and submit your first job!")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        pending_count = len([j for j in jobs if j["status"] == "pending"])
        running_count = len([j for j in jobs if j["status"] == "running"])
        completed_count = len([j for j in jobs if j["status"] == "completed"])
        failed_count = len([j for j in jobs if j["status"] == "failed"])

        with col1:
            st.metric("⏸️ Pending", pending_count)
        with col2:
            st.metric("🔄 Running", running_count)
        with col3:
            st.metric("✅ Completed", completed_count)
        with col4:
            st.metric("❌ Failed", failed_count)

        st.divider()

        # Display jobs
        for job in jobs:
            status = job["status"]

            # Status emoji
            status_emoji = {
                "pending": "⏸️",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫",
            }.get(status, "❓")

            # Expandable job card
            with st.expander(
                f"{status_emoji} {job['strategy_name']} - {job['universe_name']} ({status.upper()})",
                expanded=(status in ["running", "pending"]),
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Job ID:** `{job['id'][:16]}...`")
                    st.markdown(f"**Strategy:** {job['strategy_name']}")
                    st.markdown(f"**Universe:** {job['universe_name']}")

                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(job["created_at"])
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        time_str = job["created_at"][:19]

                    st.markdown(f"**Created:** {time_str}")

                    # Progress
                    if status == "running":
                        progress = job.get("progress", 0)
                        stocks_processed = job.get("stocks_processed", 0)
                        stocks_total = job.get("stocks_total", 0)

                        st.progress(progress / 100.0)
                        st.caption(
                            f"Progress: {stocks_processed}/{stocks_total} stocks ({progress}%)"
                        )

                    # Results summary
                    if status == "completed" and job.get("result_summary"):
                        summary = job["result_summary"]

                        st.markdown("**Results:**")
                        cols = st.columns(4)
                        cols[0].metric("Total", summary.get("total_stocks", 0))
                        cols[1].metric("🟢 BUY", summary.get("buy_count", 0))
                        cols[2].metric("🟡 HOLD", summary.get("hold_count", 0))
                        cols[3].metric("🔴 SELL", summary.get("sell_count", 0))

                    # Error message
                    if status == "failed" and job.get("error_message"):
                        st.error(f"❌ Error: {job['error_message']}")

                with col2:
                    # Action buttons
                    if status == "completed":
                        if st.button(
                            "📊 View Results",
                            key=f"view_{job['id']}",
                            use_container_width=True,
                        ):
                            # Load results into session state
                            results_data = job.get("results")
                            if results_data:
                                # Results are already deserialized as list of dicts
                                results_df = pd.DataFrame(results_data)

                                st.session_state["screening_results"] = results_df
                                st.session_state["screening_date"] = (
                                    datetime.fromisoformat(job["completed_at"]).date()
                                )
                                st.session_state["screening_strategy"] = job[
                                    "strategy_name"
                                ]

                                # ✅ NAVIGATE BACK TO SCREENING
                                st.session_state["current_page"] = "screening"
                                st.rerun()
                            else:
                                st.error("❌ No results data found for this job")

                    elif status == "pending":
                        if st.button(
                            "❌ Cancel",
                            key=f"cancel_{job['id']}",
                            use_container_width=True,
                        ):
                            if queue.cancel_job(job["id"], current_user):
                                st.success("✅ Job cancelled")
                                st.rerun()
                            else:
                                st.error("❌ Failed to cancel")

                    # Delete button
                    if status in ["completed", "failed", "cancelled", "running"]:
                        button_label = (
                            "🗑️ Force Delete" if status == "running" else "🗑️ Delete"
                        )
                        button_help = (
                            "Force delete stuck job"
                            if status == "running"
                            else "Delete this job"
                        )

                        if st.button(
                            button_label,
                            key=f"delete_{job['id']}",
                            use_container_width=True,
                            help=button_help,
                        ):
                            if queue.delete_job(job["id"], current_user):
                                st.success("✅ Job deleted")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")

        # Auto-refresh and auto-process
        if auto_refresh and (running_count > 0 or pending_count > 0):
            # AUTO-PROCESS pending jobs
            if pending_count > 0:
                try:
                    from backend.jobs.screening_worker import ScreeningWorker

                    worker = ScreeningWorker(poll_interval=0)
                    worker._process_next_job()
                except:
                    pass  # Fail silently, will retry on next refresh

            # Refresh UI
            time.sleep(10)
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading jobs: {str(e)}")
        with st.expander("🔍 Error Details"):
            import traceback

            st.code(traceback.format_exc())
