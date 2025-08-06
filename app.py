# app.py
import streamlit as st

st.set_page_config(page_title="Pnaseer Toolkit", layout="wide")
from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

from modules.inputs import show as show_input
from modules.optimization import show as show_optimization
from modules.results import show as show_results
from modules.data_management import show as show_data_management


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
    else:
        st.sidebar.markdown("**Job Status: No job selected**")
        _show_status("Input data ready", False)
        _show_status("Model selected", False)
        _show_status("Optimization completed", False)

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
