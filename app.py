class Job:
    """Job class to manage datasets for each analysis job"""
    def __init__(self, name):
        self.name = name
        self.api_dataset = None
        self.target_profile_dataset = None
        self.model_dataset = None
        self.result_dataset = None
        self.created_at = st.session_state.get('current_time', 'Unknown')
    
    def has_api_data(self):
        return self.api_dataset is not None
    
    def has_target_data(self):
        return self.target_profile_dataset is not None
    
    def has_model_data(self):
        return self.model_dataset is not None
    
    def has_result_data(self):
        return self.result_dataset is not None
    
    def has_evaluation_diagrams(self):
        """Check if evaluation diagrams data exists in results"""
        return (self.has_result_data() and 
                'evaluation_diagrams' in self.result_dataset)
    
    def get_input_status(self):
        """Check if both API and target data are present"""
        return self.has_api_data() and self.has_target_data()
    
    def get_model_status(self):
    """Check if model data is present"""
        return self.has_model_data()
    
# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Pnaseer Toolkit", layout="wide")
from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

from modules.inputs import show as show_input
from modules.optimization import show as show_optimization
from modules.results import show as show_results
from modules.data_management import show as show_data_management


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


class Job:
    """Job class to manage datasets for each analysis job"""
    def __init__(self, name):
        self.name = name
        self.api_dataset = None
        self.target_profile_dataset = None
        self.model_dataset = None
        self.result_dataset = None
        self.created_at = st.session_state.get('current_time', 'Unknown')
    
    def has_api_data(self):
        return self.api_dataset is not None
    
    def has_target_data(self):
        return self.target_profile_dataset is not None
    
    def has_model_data(self):
        return self.model_dataset is not None
    
    def has_result_data(self):
        return self.result_dataset is not None
    
    def has_evaluation_diagrams(self):
        """Check if evaluation diagrams data exists in results"""
        # Check if evaluation diagrams exist in result dataset
        return (self.has_result_data() and 
                'evaluation_diagrams' in self.result_dataset)
    
    def get_input_status(self):
        """Check if both API and target data are present"""
        return self.has_api_data() and self.has_target_data()
    
    def get_model_status(self):
        """Check if model data is present"""
        return self.has_model_data()
    
    def get_result_status(self):
        """Check if result data is present"""
        return self.has_result_data()


def _show_status(label: str, flag: bool):
    color = "green" if flag else "red"
    st.sidebar.markdown(
        f"""
        <div class="status-indicator" style="display:flex; align-items:center; margin-bottom:1px;">
          <span style="flex:1;">{label}</span>
          <span style="
            display:inline-block;
            width:12px; height:12px;
            background:{color};
            border:1px solid #333;
          "></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main(): 
    # uniform sidebar button height
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"] button {
            height: 2.5rem; 
            width: var(--sidebar-button-width) !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize jobs store
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    
    if "current_job" not in st.session_state:
        st.session_state.current_job = None

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Input Conditions"

    st.sidebar.title("Menu")
    if st.sidebar.button("Input Conditions"):
        st.session_state.current_tab = "Input Conditions"
    if st.sidebar.button("Optimization"):
        st.session_state.current_tab = "Optimization"
    if st.sidebar.button("Result"):
        st.session_state.current_tab = "Results"
    if st.sidebar.button("Data Management"):
        st.session_state.current_tab = "Data Management"

    st.sidebar.markdown("<br><br>--------------------------------------", unsafe_allow_html=True)
    
    # Persistent Storage Section
    st.sidebar.markdown("**Persistent Storage**")
    
    # Save permanent button
    if st.sidebar.button("💾 Save Permanent", key="save_permanent"):
        if st.session_state.current_job and st.session_state.current_job in st.session_state.jobs:
            current_job = st.session_state.jobs[st.session_state.current_job]
            success, result = save_job_to_file(current_job, st.session_state.current_job)
            
            if success:
                st.success(f"✅ Job '{st.session_state.current_job}' saved permanently!")
                st.info(f"📁 Saved to: {result}")
            else:
                st.error(f"❌ Failed to save job: {result}")
        else:
            st.error("❌ No job selected to save")
    
    # Load saved jobs
    saved_jobs = get_saved_jobs()
    if saved_jobs:
        st.sidebar.markdown("**Load Saved Jobs**")
        
        # Create options for selectbox
        job_options = [""] + [f"{job['name']} ({job['modified']})" for job in saved_jobs]
        selected_saved = st.sidebar.selectbox(
            "Select saved job:",
            job_options,
            key="saved_job_selector"
        )
        
        if selected_saved and selected_saved != "":
            # Extract job name from selection
            selected_job_name = selected_saved.split(" (")[0]
            
            # Find the corresponding job file
            selected_job_file = None
            for job in saved_jobs:
                if job["name"] == selected_job_name:
                    selected_job_file = job
                    break
            
            if selected_job_file:
                col1, col2 = st.sidebar.columns(2)
                
                with col1:
                    if st.button("📂 Load", key="load_saved_job"):
                        loaded_job, saved_time = load_job_from_file(selected_job_file["filepath"])
                        
                        if loaded_job:
                            # Add loaded job to session
                            st.session_state.jobs[loaded_job.name] = loaded_job
                            st.session_state.current_job = loaded_job.name
                            
                            st.success(f"✅ Job '{loaded_job.name}' loaded successfully!")
                            st.info(f"📅 Originally saved: {saved_time}")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to load job: {saved_time}")
                
                with col2:
                    if st.button("🗑️ Delete", key="delete_saved_job"):
                        try:
                            os.remove(selected_job_file["filepath"])
                            st.success(f"✅ Deleted '{selected_job_name}'")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete: {str(e)}")
        
        # Show saved jobs info
        if len(saved_jobs) > 0:
            with st.sidebar.expander(f"📋 Saved Jobs ({len(saved_jobs)})", expanded=False):
                for job in saved_jobs[:5]:  # Show first 5 jobs
                    st.write(f"• **{job['name']}**")
                    st.write(f"  📅 {job['modified']}")
                if len(saved_jobs) > 5:
                    st.write(f"... and {len(saved_jobs) - 5} more")
    else:
        st.sidebar.info("No saved jobs found")
    
    # Job Management Section
    st.sidebar.markdown("**Job Management**")
    
    # Create Job Section - Vertical Layout
    job_name = st.sidebar.text_input("Job Name", key="new_job_name", label_visibility="collapsed", placeholder="Enter job name")
    if st.sidebar.button("Create Job", key="create_job"):
        if job_name and job_name not in st.session_state.jobs:
            import datetime
            st.session_state.current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_job = Job(job_name)
            st.session_state.jobs[job_name] = new_job
            st.session_state.current_job = job_name
            st.success(f"Job '{job_name}' created!")
            st.rerun()
        elif job_name in st.session_state.jobs:
            st.error("Job name already exists!")
        else:
            st.error("Please enter a job name!")

    # Job Selection
    job_names = list(st.session_state.jobs.keys())
    if job_names:
        selected_job = st.sidebar.selectbox(
            "Select Active Job",
            [""] + job_names,
            index=(job_names.index(st.session_state.current_job) + 1) if st.session_state.current_job in job_names else 0,
            key="job_selector"
        )
        
        if selected_job and selected_job != st.session_state.current_job:
            st.session_state.current_job = selected_job
            st.rerun()
    else:
        st.sidebar.info("No jobs created yet.")

    st.sidebar.markdown("<br>--------------------------------------", unsafe_allow_html=True)

    # Status indicators for current job
    if st.session_state.current_job and st.session_state.current_job in st.session_state.jobs:
        current_job = st.session_state.jobs[st.session_state.current_job]
        st.sidebar.markdown(f"**Job Status: {st.session_state.current_job}**")
        
        _show_status("Input data ready", current_job.get_input_status())
        _show_status("Model selected", current_job.get_model_status())
        _show_status("Optimization completed", current_job.get_result_status())
        _show_status("Evaluation completed", current_job.has_evaluation_diagrams())  # Updated for new evaluation system
    else:
        st.sidebar.markdown("**Job Status: No job selected**")
        _show_status("Input data ready", False)
        _show_status("Model selected", False)
        _show_status("Optimization completed", False)
        _show_status("Evaluation completed", False)  # Updated for new evaluation system

    # render pages
    tab = st.session_state.current_tab
    if   tab == "Input Conditions":
        show_input()
    elif tab == "Optimization":
        show_optimization()
    elif tab == "Results":
        show_results()
    else:
        show_data_management()

if __name__ == "__main__":

    main()


