# modules/job_management.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def save_job_to_file(job, job_name):
    """Save job to JSON file"""
    try:
        # Create saved_jobs directory if it doesn't exist
        os.makedirs("saved_jobs", exist_ok=True)
        
        # Convert job to serializable format
        job_data = {
            "name": job.name,
            "created_at": job.created_at,
            "api_dataset": job.api_dataset.to_dict('records') if job.api_dataset is not None else None,
            "target_profile_dataset": {k: v.to_dict('records') for k, v in job.target_profile_dataset.items()} if job.target_profile_dataset is not None else None,
            "model_dataset": {k: v.to_dict('records') for k, v in job.model_dataset.items()} if job.model_dataset is not None else None,
            "result_dataset": job.result_dataset,
            "saved_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Handle pandas DataFrames in result_dataset
        if job_data["result_dataset"] is not None:
            result_data = job_data["result_dataset"].copy()
            
            # Convert DataFrames to dict format
            if "selected_api_data" in result_data and hasattr(result_data["selected_api_data"], 'to_dict'):
                result_data["selected_api_data"] = result_data["selected_api_data"].to_dict('records')
            if "selected_target_data" in result_data and hasattr(result_data["selected_target_data"], 'to_dict'):
                result_data["selected_target_data"] = result_data["selected_target_data"].to_dict('records')
            if "model_data" in result_data and hasattr(result_data["model_data"], 'to_dict'):
                result_data["model_data"] = result_data["model_data"].to_dict('records')
                
            job_data["result_dataset"] = result_data
        
        # Save to file
        filename = f"saved_jobs/{job_name}.json"
        with open(filename, 'w') as f:
            json.dump(job_data, f, indent=2)
        
        return True, filename
    except Exception as e:
        return False, str(e)

def load_job_from_file(filename):
    """Load job from JSON file"""
    try:
        with open(filename, 'r') as f:
            job_data = json.load(f)
        
        # Import Job class from app
        from app import Job
        
        # Create new job object
        job = Job(job_data["name"])
        job.created_at = job_data["created_at"]
        
        # Restore datasets
        if job_data["api_dataset"] is not None:
            job.api_dataset = pd.DataFrame(job_data["api_dataset"])
            
        if job_data["target_profile_dataset"] is not None:
            job.target_profile_dataset = {k: pd.DataFrame(v) for k, v in job_data["target_profile_dataset"].items()}
            
        if job_data["model_dataset"] is not None:
            job.model_dataset = {k: pd.DataFrame(v) for k, v in job_data["model_dataset"].items()}
        
        # Restore result dataset
        if job_data["result_dataset"] is not None:
            result_data = job_data["result_dataset"].copy()
            
            # Convert back to DataFrames
            if "selected_api_data" in result_data and result_data["selected_api_data"] is not None:
                result_data["selected_api_data"] = pd.DataFrame(result_data["selected_api_data"])
            if "selected_target_data" in result_data and result_data["selected_target_data"] is not None:
                result_data["selected_target_data"] = pd.DataFrame(result_data["selected_target_data"])
            if "model_data" in result_data and result_data["model_data"] is not None:
                result_data["model_data"] = pd.DataFrame(result_data["model_data"])
                
            job.result_dataset = result_data
        
        return job, job_data.get("saved_timestamp", "Unknown")
    except Exception as e:
        return None, str(e)

def get_saved_jobs():
    """Get list of saved job files"""
    try:
        if not os.path.exists("saved_jobs"):
            return []
        
        saved_files = []
        for filename in os.listdir("saved_jobs"):
            if filename.endswith(".json"):
                job_name = filename[:-5]  # Remove .json extension
                filepath = f"saved_jobs/{filename}"
                # Get file modification time
                mtime = os.path.getmtime(filepath)
                saved_files.append({
                    "name": job_name,
                    "filename": filename,
                    "filepath": filepath,
                    "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Sort by modification time (newest first)
        saved_files.sort(key=lambda x: x["modified"], reverse=True)
        return saved_files
    except Exception:
        return []

def _show_status_large(label: str, flag: bool):
    """Large status indicator for main page"""
    color = "green" if flag else "red"
    icon = "✅" if flag else "❌"
    st.markdown(
        f"""
        <div style="
            display: flex; 
            align-items: center; 
            padding: 10px; 
            margin: 5px 0; 
            border: 1px solid {color}; 
            border-radius: 5px;
            background-color: {'#f0f8f0' if flag else '#f8f0f0'};
        ">
            <span style="font-size: 1.2em; margin-right: 10px;">{icon}</span>
            <span style="flex: 1; font-weight: bold;">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def show():
    st.header("Job Management")
    # st.info("Create, manage, and organize your analysis jobs")

    st.divider()

    # Top section: Current Job Overview
    if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        st.markdown(f"## Current Job Status")
        st.markdown(f"**Name:** {st.session_state.current_job}")
        st.markdown(f"**Created:** {current_job.created_at}")
        
        # Job status with large indicators
        col1, col2 = st.columns(2)
        with col1:
            _show_status_large("Input Data Ready", current_job.get_input_status())
            _show_status_large("Model Selected", current_job.get_model_status())
        with col2:
            _show_status_large("Optimization Completed", current_job.get_result_status())
            _show_status_large("Evaluation Completed", current_job.has_evaluation_diagrams())
        
        # Save current job section
        st.markdown("### 💾 Save Current Job")


        if st.button("💾 Save Job Permanently", key="save_current_job", help="Save this job permanently"):
            success, result = save_job_to_file(current_job, st.session_state.current_job)
            if success:
                st.success(f"✅ Job '{st.session_state.current_job}' saved permanently!")
                st.info(f"📁 Saved to: {result}")
            else:
                st.error(f"❌ Failed to save job: {result}")
    else:
        st.warning("⚠️ No job currently selected. Create or select a job below.")

    st.divider()

    # Two-column layout for job management
    col_left, col_right = st.columns(2)

    # ═══ LEFT COLUMN: Create & Manage Jobs ══════════════════════════════════
    with col_left:
        st.markdown("## 🏗️ Create & Manage Jobs")
        
        # Create new job section
        st.markdown("### ➕ Create New Job")
        job_name = st.text_input("Job Name", placeholder="Enter a descriptive job name", key="new_job_name")
        
        col_create, col_select = st.columns(2)
        with col_create:
            if st.button("➕ Create Job", key="create_job"):
                if job_name and job_name not in st.session_state.get("jobs", {}):
                    # Import Job class from app
                    from app import Job
                    
                    import datetime
                    st.session_state.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_job = Job(job_name)
                    
                    # Initialize jobs dict if needed
                    if "jobs" not in st.session_state:
                        st.session_state.jobs = {}
                    
                    st.session_state.jobs[job_name] = new_job
                    st.session_state.current_job = job_name
                    st.success(f"✅ Job '{job_name}' created and activated!")
                    st.rerun()
                elif job_name in st.session_state.get("jobs", {}):
                    st.error("❌ Job name already exists!")
                else:
                    st.error("❌ Please enter a job name!")
        
        # Select existing job section
        st.markdown("### 🔄 Switch Active Job")
        jobs = st.session_state.get("jobs", {})
        job_names = list(jobs.keys())
        
        if job_names:
            current_selection = st.session_state.get("current_job", "")
            current_index = job_names.index(current_selection) if current_selection in job_names else -1
            
            selected_job = st.selectbox(
                "Select Job",
                job_names,
                index=current_index if current_index >= 0 else 0,
                key="job_selector_main"
            )
            
            if st.button("🔄 Switch to This Job", key="switch_job"):
                if selected_job != st.session_state.get("current_job"):
                    st.session_state.current_job = selected_job
                    st.success(f"✅ Switched to job: {selected_job}")
                    st.rerun()
                else:
                    st.info("💡 This job is already active")
        else:
            st.info("💡 No jobs in current session. Create your first job above!")

    # ═══ RIGHT COLUMN: Load Saved Jobs ══════════════════════════════════════
    with col_right:
        st.markdown("## 💾 Saved Jobs")
        
        saved_jobs = get_saved_jobs()
        
        if saved_jobs:
            st.markdown(f"### 📂 Available Saved Jobs ({len(saved_jobs)})")
            
            # Load saved job section
            job_options = [""] + [f"{job['name']} ({job['modified']})" for job in saved_jobs]
            selected_saved = st.selectbox(
                "Select Saved Job",
                job_options,
                key="saved_job_selector_main"
            )
            
            if selected_saved and selected_saved != "":
                selected_job_name = selected_saved.split(" (")[0]
                selected_job_file = None
                
                for job in saved_jobs:
                    if job["name"] == selected_job_name:
                        selected_job_file = job
                        break
                
                # if selected_job_file:
                #     # Show job details
                #     st.markdown(f"**Selected:** {selected_job_name}")
                #     st.markdown(f"**Last Modified:** {selected_job_file['modified']}")
                    
                    col_load, col_delete = st.columns(2)
                    
                    with col_load:
                        if st.button("📂 Load Job", key="load_saved_job_main"):
                            loaded_job, saved_time = load_job_from_file(selected_job_file["filepath"])
                            
                            if loaded_job:
                                # Initialize jobs dict if needed
                                if "jobs" not in st.session_state:
                                    st.session_state.jobs = {}
                                
                                # Add loaded job to session
                                st.session_state.jobs[loaded_job.name] = loaded_job
                                st.session_state.current_job = loaded_job.name
                                
                                st.success(f"✅ Job '{loaded_job.name}' loaded and activated!")
                                st.info(f"📅 Originally saved: {saved_time}")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to load job: {saved_time}")
                    
                    with col_delete:
                        if st.button("🗑️ Delete", key="delete_saved_job_main"):
                            try:
                                os.remove(selected_job_file["filepath"])
                                st.success(f"✅ Deleted '{selected_job_name}' from saved jobs")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to delete: {str(e)}")
            
            # List all saved jobs
            st.markdown("### 📚 All Saved Jobs")
            for job in saved_jobs:
                with st.expander(f"📄 {job['name']}", expanded=False):
                    st.write(f"**Saved:** {job['modified']}")
                    st.write(f"**File:** {job['filename']}")
                    
                    col_quick_load, col_quick_delete = st.columns(2)
                    with col_quick_load:
                        if st.button("📂 Quick Load", key=f"quick_load_{job['name']}"):
                            loaded_job, saved_time = load_job_from_file(job["filepath"])
                            if loaded_job:
                                if "jobs" not in st.session_state:
                                    st.session_state.jobs = {}
                                st.session_state.jobs[loaded_job.name] = loaded_job
                                st.session_state.current_job = loaded_job.name
                                st.success(f"✅ Loaded '{loaded_job.name}'!")
                                st.rerun()
                    with col_quick_delete:
                        if st.button("🗑️ Quick Delete", key=f"quick_delete_{job['name']}"):
                            try:
                                os.remove(job["filepath"])
                                st.success(f"✅ Deleted '{job['name']}'")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed: {str(e)}")
        else:
            st.info("💡 No saved jobs found. Save your current jobs to make them persistent across sessions.")
            
            # Tips for users
            st.markdown("### 💡 Getting Started")
            st.markdown("""
            **To save jobs permanently:**
            1. Create a job using the form on the left
            2. Work on your analysis (import data, run optimization)
            3. Use the "💾 Save Job Permanently" button above
            4. Your job will appear here for future loading
            """)
