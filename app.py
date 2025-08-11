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
        st.session_state.current_tab = "Job Management"

    # ═══ SIMPLIFIED SIDEBAR ══════════════════════════════════════════════════
    st.sidebar.title("🧪 Pnaseer Toolkit")
    
    # Main navigation
    st.sidebar.markdown("### 📋 Main Menu")
    if st.sidebar.button("💼 Job Management"):
        st.session_state.current_tab = "Job Management"
    if st.sidebar.button("🗂️ Database management"):
        st.session_state.current_tab = "Database management"
    if st.sidebar.button("📥 Input Target"):
        st.session_state.current_tab = "Input Target"
    if st.sidebar.button("⚙️ Calculation"):
        st.session_state.current_tab = "Calculation"
    if st.sidebar.button("📊 Results"):
        st.session_state.current_tab = "Results"

    # Current job indicator (minimal)
    st.sidebar.markdown("---")
    if st.session_state.current_job:
        st.sidebar.markdown(f"**🔸 Active Job:** {st.session_state.current_job}")
    else:
        st.sidebar.markdown("**🔹 No Active Job**")
        st.sidebar.info("💡 Visit Job Management to create or select a job")

    # Quick status (minimal)
    if (st.session_state.current_job and 
        st.session_state.current_job in st.session_state.jobs):
        
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        st.sidebar.markdown("**📈 Quick Status:**")
        status_items = [
            ("Input", current_job.get_input_status()),
            ("Model", current_job.get_model_status()),
            ("Calculation", current_job.get_result_status()),
            ("Evaluation", current_job.has_evaluation_diagrams())
        ]
        
        status_text = " | ".join([f"{name}: {'✅' if status else '❌'}" for name, status in status_items])
        st.sidebar.markdown(f"<small>{status_text}</small>", unsafe_allow_html=True)

    # # App info
    # st.sidebar.markdown("---")
    # st.sidebar.markdown("**ℹ️ About**")
    # st.sidebar.markdown("<small>Pharmaceutical formulation optimization toolkit</small>", unsafe_allow_html=True)

    # ═══ RENDER PAGES ════════════════════════════════════════════════════════
    tab = st.session_state.current_tab
    if tab == "Job Management":
        show_job_management()
    elif tab == "Database management":
        show_data_management()
    elif tab == "Input Target":
        show_input()
    elif tab == "Calculation":
        show_optimization()
    elif tab == "Results":
        show_results()

if __name__ == "__main__":
    main()
