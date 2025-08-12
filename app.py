# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pnaseer Toolkit", layout="wide")
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
    
    def get_result_status(self):
        """Check if result data is present"""
        return self.has_result_data()


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

    # ═══ SIMPLIFIED SIDEBAR ══════════════════════════════════════════════════
    st.sidebar.title("Pnaseer Toolkit")
    
    # Main navigation
    st.sidebar.markdown("### Main Menu")
    if st.sidebar.button("Manage\nJob"):
        st.session_state.current_tab = "Manage Job"
    if st.sidebar.button("Manage\nDatabase"):
        st.session_state.current_tab = "Manage Database"
    if st.sidebar.button("Create Target\nProfile"):
        st.session_state.current_tab = "Create Target Profile"
    if st.sidebar.button("Modeling\nOptimization"):
        st.session_state.current_tab = "Modeling Optimization"
    if st.sidebar.button("Show\nResults"):
        st.session_state.current_tab = "Show Results"

    # Current job indicator (minimal)
    st.sidebar.markdown("---")
    if st.session_state.current_job:
        st.sidebar.markdown(f"**Active Job:** {st.session_state.current_job}")
    else:
        st.sidebar.markdown("**No Active Job**")

    # Quick status (minimal)
    if (st.session_state.current_job and 
        st.session_state.current_job in st.session_state.jobs):
        
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        st.sidebar.markdown("**Quick Status:**")
        status_items = [
            ("Input", current_job.get_input_status()),
            ("Model", current_job.get_model_status()),
            ("Calculation", current_job.get_result_status()),
            ("Evaluation", current_job.has_evaluation_diagrams())
        ]
        
        status_text = " | ".join([f"{name}: {'✅' if status else '❌'}" for name, status in status_items])
        st.sidebar.markdown(f"<small>{status_text}</small>", unsafe_allow_html=True)

    # ═══ RENDER PAGES ════════════════════════════════════════════════════════
    tab = st.session_state.current_tab
    if tab == "Manage Job":
        show_job_management()
    elif tab == "Manage Database":
        show_data_management()
    elif tab == "Create Target Profile":
        show_input()
    elif tab == "Modeling Optimization":
        show_optimization()
    elif tab == "Show Results":
        show_results()

if __name__ == "__main__":
    main()
