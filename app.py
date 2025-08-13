# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pnaseer DDS Optimization", layout="wide")
from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

from modules.inputs import show as show_input
from modules.optimization import show as show_optimization
from modules.results import show as show_results
from modules.data_management import show as show_data_management
from modules.job_management import show as show_job_management


class Job:
    """Job class to manage datasets for each analysis job"""
    def __init__(self, name):
        self.name = name
        self.api_dataset = None
        self.target_profile_dataset = None
        self.model_dataset = None
        self.result_dataset = None
        self.created_at = st.session_state.get('current_time', 'Unknown')
        
        # Add database storage to Job for persistence
        self.common_api_datasets = {}
        self.polymer_datasets = {}
        self.complete_target_profiles = {}
        
        # Add formulation-specific results storage
        self.formulation_results = {}  # {profile_name: {formulation_name: result_data}}
        
        # Add optimization progress storage (NEW)
        self.optimization_progress = {}  # {progress_id: progress_data}
        self.current_optimization_progress = None  # Active optimization progress
    
    def has_api_data(self):
        return self.api_dataset is not None
    
    def has_target_data(self):
        return self.target_profile_dataset is not None
    
    def has_model_data(self):
        return self.model_dataset is not None
    
    def has_result_data(self):
        return self.result_dataset is not None or bool(self.formulation_results) or bool(self.optimization_progress)
    
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
    
    def get_result_status(self):
        """Check if result data is present"""
        return self.has_result_data()
    
    def get_formulation_result(self, profile_name, formulation_name):
        """Get results for a specific formulation"""
        if profile_name in self.formulation_results:
            return self.formulation_results[profile_name].get(formulation_name)
        return None
    
    def set_formulation_result(self, profile_name, formulation_name, result_data):
        """Set results for a specific formulation"""
        if profile_name not in self.formulation_results:
            self.formulation_results[profile_name] = {}
        self.formulation_results[profile_name][formulation_name] = result_data
    
    def has_formulation_results(self, profile_name, formulation_name):
        """Check if specific formulation has results"""
        return (profile_name in self.formulation_results and 
                formulation_name in self.formulation_results[profile_name])
    
    # NEW: Optimization Progress Methods
    def save_optimization_progress(self, progress_data):
        """Save current optimization progress"""
        self.current_optimization_progress = progress_data
    
    def get_optimization_progress(self):
        """Get current optimization progress"""
        return self.current_optimization_progress
    
    def clear_optimization_progress(self):
        """Clear current optimization progress"""
        self.current_optimization_progress = None
    
    def has_optimization_progress(self):
        """Check if there is saved optimization progress"""
        return self.current_optimization_progress is not None


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


def sync_all_data_with_job():
    """Sync ALL data between session state and current job for persistence after browser refresh"""
    if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        # Ensure all attributes exist
        current_job = ensure_job_attributes(current_job)
        
        # 1. FORCE sync databases from job to session state - this is the key fix for refresh persistence
        if current_job.common_api_datasets:
            st.session_state["common_api_datasets"] = current_job.common_api_datasets.copy()
        elif "common_api_datasets" not in st.session_state:
            st.session_state["common_api_datasets"] = {}
            
        if current_job.polymer_datasets:
            st.session_state["polymer_datasets"] = current_job.polymer_datasets.copy()
        elif "polymer_datasets" not in st.session_state:
            st.session_state["polymer_datasets"] = {}
        
        # 2. Target profiles, optimization progress, and results are accessed directly from job
        # No session state sync needed since modules access current_job directly
        
        # DEBUG: Add session state debug info (can be removed later)
        if "debug_sync_count" not in st.session_state:
            st.session_state.debug_sync_count = 0
        st.session_state.debug_sync_count += 1
        st.session_state.debug_last_sync = f"Sync #{st.session_state.debug_sync_count}: Job={current_job.name}, Profiles={len(current_job.complete_target_profiles)}, Progress={'Yes' if current_job.current_optimization_progress else 'No'}"
        
        # Update the job in session state
        st.session_state.jobs[st.session_state.current_job] = current_job


def save_all_data_to_job():
    """Save ALL data from session state to current job for persistence"""
    if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        # Ensure all attributes exist
        current_job = ensure_job_attributes(current_job)
        
        # 1. FORCE save databases from session state to job (ALWAYS sync)
        if "common_api_datasets" in st.session_state:
            current_job.common_api_datasets = st.session_state["common_api_datasets"].copy()
        if "polymer_datasets" in st.session_state:
            current_job.polymer_datasets = st.session_state["polymer_datasets"].copy()
        
        # 2. Target profiles, optimization progress, and results are already saved directly to job
        # But ensure the job reference in session state is current
        
        # 3. FORCE update the job in session state to ensure persistence
        st.session_state.jobs[st.session_state.current_job] = current_job


def sync_databases_with_job():
    """LEGACY: Sync database data between session state and current job for persistence"""
    # This function is kept for backward compatibility but now calls the comprehensive sync
    sync_all_data_with_job()


def save_databases_to_job():
    """LEGACY: Save database data from session state to current job for persistence"""  
    # This function is kept for backward compatibility but now calls the comprehensive save
    save_all_data_to_job()


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

    # Initialize session state
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    
    if "current_job" not in st.session_state:
        st.session_state.current_job = None

    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "Manage Job"
    
    # DEBUG: Add debug session state tracking
    if "app_refresh_count" not in st.session_state:
        st.session_state.app_refresh_count = 0
    st.session_state.app_refresh_count += 1
    
    # Sync ALL data with current job for persistence (COMPREHENSIVE SYNC)
    sync_all_data_with_job()

    # ═══ SIMPLIFIED SIDEBAR ══════════════════════════════════════════════════
    st.sidebar.title("Pnaseer DDS Optimization")
    
    # DEBUG: Show app state info
    with st.sidebar.expander("🔍 Debug App State", expanded=False):
        st.write(f"**App Refresh Count:** {st.session_state.app_refresh_count}")
        if st.session_state.get("debug_last_sync"):
            st.write(f"**Last Sync:** {st.session_state.debug_last_sync}")
        if st.session_state.get("current_job"):
            current_job = st.session_state.jobs.get(st.session_state.current_job)
            if current_job:
                st.write(f"**Current Job:** {current_job.name}")
                st.write(f"**Target Profiles:** {len(current_job.complete_target_profiles)}")
                st.write(f"**Optimization Progress:** {'Yes' if current_job.current_optimization_progress else 'No'}")
                st.write(f"**API Datasets:** {len(current_job.common_api_datasets)}")
                st.write(f"**Session API:** {len(st.session_state.get('common_api_datasets', {}))}")
    
    # Main navigation
    st.sidebar.markdown("### Main Menu")
    if st.sidebar.button("Manage\nJob"):
        st.session_state.current_tab = "Manage Job"
    if st.sidebar.button("Manage\nDatabase"):
        st.session_state.current_tab = "Manage Database"
    if st.sidebar.button("Manage Target\nProfile"):
        st.session_state.current_tab = "Manage Target Profile"
    if st.sidebar.button("Modeling\nOptimization"):
        st.session_state.current_tab = "Modeling Optimization"
    if st.sidebar.button("Show\nResults"):
        st.session_state.current_tab = "Show Results"

    # Current job indicator with job switching capability
    st.sidebar.markdown("---")
    if st.session_state.get("jobs"):
        job_names = list(st.session_state.jobs.keys())
        if st.session_state.current_job and st.session_state.current_job in job_names:
            current_index = job_names.index(st.session_state.current_job)
        else:
            current_index = 0 if job_names else None
            
        if job_names:
            selected_job = st.sidebar.selectbox(
                "**Active Job:**",
                job_names,
                index=current_index,
                key="job_switcher"
            )
            
            # Switch job if selection changed
            if selected_job != st.session_state.current_job:
                # Save current job data before switching (COMPREHENSIVE SAVE)
                save_all_data_to_job()
                
                # Switch to new job
                st.session_state.current_job = selected_job
                
                # Sync new job data to session state (COMPREHENSIVE SYNC)
                sync_all_data_with_job()
                st.rerun()
        else:
            st.sidebar.markdown("**No Jobs Available**")
    else:
        st.sidebar.markdown("**No Jobs Available**")

    # ═══ RENDER PAGES ════════════════════════════════════════════════════════
    # Save ALL data to job before rendering pages (COMPREHENSIVE SAVE)
    save_all_data_to_job()
    
    tab = st.session_state.current_tab
    if tab == "Manage Job":
        show_job_management()
    elif tab == "Manage Database":
        show_data_management()
    elif tab == "Manage Target Profile":
        show_input()
    elif tab == "Modeling Optimization":
        show_optimization()
    elif tab == "Show Results":
        show_results()

if __name__ == "__main__":
    main()
