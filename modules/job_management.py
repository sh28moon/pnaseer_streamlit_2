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
        
        # Initialize new attributes for existing jobs if they don't exist
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
        
        # Convert job to serializable format
        job_data = {
            "name": job.name,
            "created_at": job.created_at,
            "api_dataset": job.api_dataset.to_dict('records') if job.api_dataset is not None else None,
            "target_profile_dataset": {k: v.to_dict('records') for k, v in job.target_profile_dataset.items()} if job.target_profile_dataset is not None else None,
            "model_dataset": {k: v.to_dict('records') for k, v in job.model_dataset.items()} if job.model_dataset is not None else None,
            "result_dataset": job.result_dataset,
            "saved_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            
            # Include database data for persistence
            "common_api_datasets": {k: v.to_dict('records') for k, v in job.common_api_datasets.items()} if job.common_api_datasets else {},
            "polymer_datasets": {k: v.to_dict('records') for k, v in job.polymer_datasets.items()} if job.polymer_datasets else {},
            
            # Include formulation-specific results
            "formulation_results": job.formulation_results if hasattr(job, 'formulation_results') else {},
            
            # Include optimization progress (NEW)
            "optimization_progress": job.optimization_progress if hasattr(job, 'optimization_progress') else {},
            "current_optimization_progress": job.current_optimization_progress if hasattr(job, 'current_optimization_progress') else None
        }
        
        # Handle complete_target_profiles with DataFrame serialization
        if hasattr(job, 'complete_target_profiles') and job.complete_target_profiles:
            serialized_profiles = {}
            for profile_name, profile_data in job.complete_target_profiles.items():
                serialized_profile = {}
                for key, value in profile_data.items():
                    if hasattr(value, 'to_dict'):  # It's a DataFrame
                        serialized_profile[key] = value.to_dict('records')
                    else:
                        serialized_profile[key] = value
                serialized_profiles[profile_name] = serialized_profile
            job_data["complete_target_profiles"] = serialized_profiles
        else:
            job_data["complete_target_profiles"] = {}
        
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
        
        # Restore database data
        if "common_api_datasets" in job_data:
            job.common_api_datasets = {k: pd.DataFrame(v) for k, v in job_data["common_api_datasets"].items()}
        else:
            job.common_api_datasets = {}
        
        if "polymer_datasets" in job_data:
            job.polymer_datasets = {k: pd.DataFrame(v) for k, v in job_data["polymer_datasets"].items()}
        else:
            job.polymer_datasets = {}
        
        # Restore complete target profiles
        if "complete_target_profiles" in job_data:
            restored_profiles = {}
            for profile_name, profile_data in job_data["complete_target_profiles"].items():
                restored_profile = {}
                for key, value in profile_data.items():
                    if key in ['api_data', 'polymer_data', 'formulation_data'] and value is not None:
                        restored_profile[key] = pd.DataFrame(value)
                    else:
                        restored_profile[key] = value
                restored_profiles[profile_name] = restored_profile
            job.complete_target_profiles = restored_profiles
        else:
            job.complete_target_profiles = {}
        
        # Restore formulation-specific results
        if "formulation_results" in job_data:
            job.formulation_results = job_data["formulation_results"]
        else:
            job.formulation_results = {}
        
        # Restore optimization progress (NEW)
        if "optimization_progress" in job_data:
            job.optimization_progress = job_data["optimization_progress"]
        else:
            job.optimization_progress = {}
        
        if "current_optimization_progress" in job_data:
            job.current_optimization_progress = job_data["current_optimization_progress"]
        else:
            job.current_optimization_progress = None
        
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

def show():
    st.header("Job Management")
    
    # Display current job information if available
    current_job_name = st.session_state.get("current_job")
    if current_job_name and current_job_name in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[current_job_name]
        
        current_job = ensure_job_attributes(current_job)
        
        # Update the job in session state
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
                # Save current job's databases before switching
                if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.jobs:
                    current_job = st.session_state.jobs[st.session_state.current_job]
                    # Initialize attributes if they don't exist
                    if not hasattr(current_job, 'common_api_datasets'):
                        current_job.common_api_datasets = {}
                    if not hasattr(current_job, 'polymer_datasets'):
                        current_job.polymer_datasets = {}
                    current_job.common_api_datasets = st.session_state.get("common_api_datasets", {})
                    current_job.polymer_datasets = st.session_state.get("polymer_datasets", {})
                
                # Import Job class from app
                from app import Job
                
                import datetime
                st.session_state.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_job = Job(job_name)
                
                # Ensure all attributes are properly initialized
                new_job = ensure_job_attributes(new_job)
                
                # Initialize jobs dict if needed
                if "jobs" not in st.session_state:
                    st.session_state.jobs = {}
                
                st.session_state.jobs[job_name] = new_job
                st.session_state.current_job = job_name
                
                # Initialize databases for new job
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
                success, result = save_job_to_file(current_job, current_job_name)
                if success:
                    pass  # Remove notification as requested
                else:
                    st.error(f"❌ Failed to save job: {result}")
            else:
                st.error("❌ No current job to save!")


    # ═══ RIGHT COLUMN: Load Saved Jobs ══════════════════════════════════════
    with col_right:        
        saved_jobs = get_saved_jobs()
        
        if saved_jobs:
            st.markdown(f"### 📂 Load Saved Jobs")
            
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
                
                # Load Job and Remove Job buttons
                col_load, col_remove = st.columns(2)
                
                with col_load:
                    if st.button("📂 Load Job", key="load_saved_job_main"):
                        loaded_job, saved_time = load_job_from_file(selected_job_file["filepath"])
                        
                        if loaded_job:
                            # Ensure job attributes are properly initialized
                            loaded_job = ensure_job_attributes(loaded_job)
                            
                            # Initialize jobs dict if needed
                            if "jobs" not in st.session_state:
                                st.session_state.jobs = {}
                            
                            # Add loaded job to session
                            st.session_state.jobs[loaded_job.name] = loaded_job
                            st.session_state.current_job = loaded_job.name
                            
                            # Sync ALL job data to session state for immediate availability
                            if not hasattr(loaded_job, 'common_api_datasets'):
                                loaded_job.common_api_datasets = {}
                            if not hasattr(loaded_job, 'polymer_datasets'):
                                loaded_job.polymer_datasets = {}
                            if not hasattr(loaded_job, 'complete_target_profiles'):
                                loaded_job.complete_target_profiles = {}
                            if not hasattr(loaded_job, 'formulation_results'):
                                loaded_job.formulation_results = {}
                            if not hasattr(loaded_job, 'optimization_progress'):
                                loaded_job.optimization_progress = {}
                            if not hasattr(loaded_job, 'current_optimization_progress'):
                                loaded_job.current_optimization_progress = None
                            
                            # COMPREHENSIVE SYNC: Sync ALL job data to session state immediately
                            st.session_state["common_api_datasets"] = loaded_job.common_api_datasets.copy()
                            st.session_state["polymer_datasets"] = loaded_job.polymer_datasets.copy()
                            
                            # Ensure ALL data is available immediately after loading
                            # Target profiles and optimization progress are accessed directly from job
                            # but we need to ensure session state has the current job reference
                            
                            # Show loaded data summary
                            profile_count = len(loaded_job.complete_target_profiles)
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
                            
                            # Force immediate sync of all data
                            st.session_state.jobs[loaded_job.name] = loaded_job
                            
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to load job: {saved_time}")
                
                with col_remove:
                    if st.button("🗑️ Remove Job", key="remove_saved_job_main"):
                        try:
                            os.remove(selected_job_file["filepath"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to remove: {str(e)}")
        else:
            st.markdown("### 📂 Load Saved Jobs")
            st.info("No saved jobs found. Create and save jobs to see them here.")
