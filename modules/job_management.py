# modules/job_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

# Import unified storage functions
from modules.storage_utils import (
    save_data_to_file, 
    load_data_from_file, 
    get_saved_data_list, 
    delete_saved_data,
    save_progress_to_job,
    clear_progress_from_job
)

def ensure_job_attributes(job):
    """Ensure all required attributes exist on a job object"""
    if not hasattr(job, 'common_api_datasets'):
        job.common_api_datasets = {}
    if not hasattr(job, 'polymer_datasets'):
        job.polymer_datasets = {}
    if not hasattr(job, 'complete_target_profiles'):
        job.complete_target_profiles = {}
    if not hasattr(job, 'formulation_results'):
        job.formulation_results = {}
    if not hasattr(job, 'optimization_progress'):
        job.optimization_progress = {}
    if not hasattr(job, 'current_optimization_progress'):
        job.current_optimization_progress = None
    return job

def force_sync_job_to_session_state(job):
    """Force comprehensive sync of job data to session state"""
    # Ensure session state has all required keys
    if "common_api_datasets" not in st.session_state:
        st.session_state["common_api_datasets"] = {}
    if "polymer_datasets" not in st.session_state:
        st.session_state["polymer_datasets"] = {}
    
    # Sync all data from job to session state
    st.session_state["common_api_datasets"] = job.common_api_datasets.copy() if job.common_api_datasets else {}
    st.session_state["polymer_datasets"] = job.polymer_datasets.copy() if job.polymer_datasets else {}

def show():
    st.header("Job Management")
    
    # Simplified storage info (no GitHub complexity)
    st.info("🏠 **Local Storage**: Jobs and databases are saved to the same location for consistency")
    
    # Display current job information if available
    current_job_name = st.session_state.get("current_job")
    if current_job_name and current_job_name in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[current_job_name]
        
        current_job = ensure_job_attributes(current_job)
        
        # Update the job in session state (ensures all data is current)
        st.session_state.jobs[current_job_name] = current_job
        
        # Show job status
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            target_profile_count = len(getattr(current_job, 'complete_target_profiles', {}))
            st.metric("Target Profiles", target_profile_count)
        
        with col_info2:
            # Count formulations with results
            formulation_result_count = 0
            if hasattr(current_job, 'formulation_results'):
                for profile_results in current_job.formulation_results.values():
                    formulation_result_count += len(profile_results)
            st.metric("Formulation Results", formulation_result_count)
        
        with col_info3:
            api_dataset_count = len(getattr(current_job, 'common_api_datasets', {}))
            polymer_dataset_count = len(getattr(current_job, 'polymer_datasets', {}))
            st.metric("Datasets", f"API: {api_dataset_count}, Polymer: {polymer_dataset_count}")
        
        # Show optimization progress status if available
        if hasattr(current_job, 'current_optimization_progress') and current_job.current_optimization_progress:
            progress = current_job.current_optimization_progress
            progress_status = progress.get('status', 'unknown')
            st.info(f"🔬 Optimization Progress: {progress_status.title()} | Target Profile: {progress.get('target_profile_name', 'None')} | Models: {progress.get('atps_model', 'None')}, {progress.get('drug_release_model', 'None')}")
        
        # Debug section (optional - can be removed later)
        with st.expander("🔍 Debug Job Data", expanded=False):
            st.write("**Current Job Data:**")
            st.write(f"- API Datasets: {list(current_job.common_api_datasets.keys()) if current_job.common_api_datasets else 'None'}")
            st.write(f"- Polymer Datasets: {list(current_job.polymer_datasets.keys()) if current_job.polymer_datasets else 'None'}")
            st.write(f"- Target Profiles: {list(current_job.complete_target_profiles.keys()) if current_job.complete_target_profiles else 'None'}")
            st.write(f"- Optimization Progress: {'Yes' if current_job.current_optimization_progress else 'None'}")
            st.write(f"- Formulation Results: {len(current_job.formulation_results)} profiles" if current_job.formulation_results else "- Formulation Results: None")
            
            st.write("**Session State Databases:**")
            st.write(f"- API: {list(st.session_state.get('common_api_datasets', {}).keys())}")
            st.write(f"- Polymer: {list(st.session_state.get('polymer_datasets', {}).keys())}")
    
    st.divider()
    
    st.markdown("## 🏗️ Create & Manage Jobs")
    
    # Two-column layout for job management
    col_left, col_right = st.columns(2)

    # ═══ LEFT COLUMN: Create & Manage Jobs ══════════════════════════════════
    with col_left:       
        
        # Create new job section
        st.markdown("### ➕ Create New Job")
        job_name = st.text_input("Job Name", placeholder="Enter a descriptive job name", key="new_job_name")
        
        if st.button("➕ Create Job", key="create_job"):
            if job_name and job_name not in st.session_state.get("jobs", {}):
                # Import Job class from app
                from app import Job
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.current_time = current_time
                new_job = Job(job_name)
                
                # Ensure all attributes are properly initialized
                new_job = ensure_job_attributes(new_job)
                
                # Initialize jobs dict if needed
                if "jobs" not in st.session_state:
                    st.session_state.jobs = {}
                
                st.session_state.jobs[job_name] = new_job
                st.session_state.current_job = job_name
                
                # Initialize empty databases for new job
                st.session_state["common_api_datasets"] = {}
                st.session_state["polymer_datasets"] = {}
                
                st.rerun()
            elif job_name in st.session_state.get("jobs", {}):
                st.error("❌ Job name already exists!")
            else:
                st.error("❌ Please enter a job name!")
        
        # Save Job button - only enabled if current job exists
        current_job_name = st.session_state.get("current_job")
        has_current_job = (current_job_name and 
                         current_job_name in st.session_state.get("jobs", {}))
        
        if st.button("💾 Save Job to Cloud", key="save_current_job", 
                    disabled=not has_current_job,
                    help="Save current job to cloud"):
            if has_current_job:
                current_job = st.session_state.jobs[current_job_name]
                
                # Ensure current data is synced to job before saving
                if "common_api_datasets" in st.session_state:
                    current_job.common_api_datasets = st.session_state["common_api_datasets"].copy()
                if "polymer_datasets" in st.session_state:
                    current_job.polymer_datasets = st.session_state["polymer_datasets"].copy()
                
                # Update job in session state
                st.session_state.jobs[current_job_name] = current_job
                
                # Save using unified storage function
                success, result = save_data_to_file(current_job, "jobs", current_job_name)
                
                if success:
                    st.success(f"✅ Job '{current_job_name}' saved successfully! Location: {result}")
                else:
                    st.error(f"❌ Failed to save job: {result}")
            else:
                st.error("❌ No current job to save!")

    # ═══ RIGHT COLUMN: Load Saved Jobs ══════════════════════════════════════
    with col_right:        
        # Get saved jobs using unified function
        saved_jobs = get_saved_data_list("jobs")
        
        if saved_jobs:
            st.markdown(f"### 📂 Load Saved Jobs")
            
            # Load saved job section
            job_options = [""] + [f"{job['save_name']} ({job['modified']})" for job in saved_jobs]
            selected_saved = st.selectbox(
                "Select Saved Job",
                job_options,
                key="saved_job_selector_main"
            )
            
            if selected_saved and selected_saved != "":
                selected_job_name = selected_saved.split(" (")[0]
                selected_job_file = None
                
                for job in saved_jobs:
                    if job["save_name"] == selected_job_name:
                        selected_job_file = job
                        break
                
                # Load Job and Remove Job buttons
                col_load, col_remove = st.columns(2)
                
                with col_load:
                    if st.button("📂 Load Job", key="load_saved_job_main"):
                        if selected_job_file:
                            # Load using unified function
                            loaded_job, saved_time, profile_count = load_data_from_file(
                                selected_job_file["filepath"], "jobs"
                            )
                            
                            if loaded_job:
                                # Ensure job attributes are properly initialized
                                loaded_job = ensure_job_attributes(loaded_job)
                                
                                # Initialize jobs dict if needed
                                if "jobs" not in st.session_state:
                                    st.session_state.jobs = {}
                                
                                # Add loaded job to session
                                st.session_state.jobs[loaded_job.name] = loaded_job
                                st.session_state.current_job = loaded_job.name
                                
                                # FORCE COMPREHENSIVE SYNC: Ensure ALL data is immediately available
                                force_sync_job_to_session_state(loaded_job)
                                
                                # Show loaded data summary
                                api_count = len(loaded_job.common_api_datasets)
                                polymer_count = len(loaded_job.polymer_datasets)
                                
                                # Count formulation results
                                formulation_result_count = 0
                                for profile_results in loaded_job.formulation_results.values():
                                    formulation_result_count += len(profile_results)
                                
                                # Check optimization progress
                                optimization_status = "None"
                                if hasattr(loaded_job, 'current_optimization_progress') and loaded_job.current_optimization_progress:
                                    optimization_status = loaded_job.current_optimization_progress.get('status', 'Unknown')
                                
                                st.success(f"""✅ Job '{loaded_job.name}' loaded successfully!
                                
**Loaded Data:**
- Target Profiles: {profile_count}
- API Datasets: {api_count}
- Polymer Datasets: {polymer_count}  
- Formulation Results: {formulation_result_count}
- Optimization Status: {optimization_status}""")
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to load job: {saved_time}")
                
                with col_remove:
                    if st.button("🗑️ Remove Job", key="remove_saved_job_main"):
                        if selected_job_file:
                            success, message = delete_saved_data(selected_job_file["filepath"])
                            if success:
                                st.success(f"✅ Removed '{selected_job_name}' successfully")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to remove: {message}")
        else:
            st.markdown("### 📂 Load Saved Jobs")
            st.info("No saved jobs found. Create and save jobs to see them here.")
    
    st.divider()
    
    # ── Progress Management Section ─────────────────────────────────────────
    st.markdown("## 💾 Progress Management")
    
    col_save_progress, col_clear_progress = st.columns(2)
    
    # Get current job
    current_job = None
    if current_job_name and current_job_name in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[current_job_name]
    
    with col_save_progress:
        st.markdown("### Save Progress")
        st.markdown("Save current job progress (same as 'Save Job to Cloud')")
        
        if st.button("💾 Save Progress", key="save_progress_main", 
                   disabled=not current_job,
                   help="Save current progress to cloud"):
            if current_job:
                success, result = save_progress_to_job(current_job)
                if success:
                    st.success(f"✅ Progress saved successfully!")
                else:
                    st.error(f"❌ Failed to save progress: {result}")
            else:
                st.error("❌ No current job to save!")
    
    with col_clear_progress:
        st.markdown("### Clear Progress")
        st.markdown("Clear optimization progress data")
        
        if st.button("🗑️ Clear Progress", key="clear_progress_main",
                   disabled=not current_job,
                   help="Clear optimization progress"):
            if current_job:
                success, result = clear_progress_from_job(current_job)
                if success:
                    # Update job in session state
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"✅ Progress cleared successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to clear progress: {result}")
            else:
                st.error("❌ No current job to clear!")
