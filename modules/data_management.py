# modules/data_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Import unified storage functions
try:
    from modules.storage_utils import (
        save_data_to_file, 
        load_data_from_file, 
        get_saved_data_list, 
        delete_saved_data,
        save_progress_to_job,
        clear_progress_from_job
    )
except ImportError:
    # Fallback if storage_utils not available yet
    st.error("Storage utilities not found. Please ensure storage_utils.py is in the modules folder.")

def sync_datasets_with_current_job():
    """Sync datasets with current job for comprehensive persistence"""
    if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        # Ensure job has dataset attributes
        if not hasattr(current_job, 'common_api_datasets'):
            current_job.common_api_datasets = {}
        if not hasattr(current_job, 'polymer_datasets'):
            current_job.polymer_datasets = {}
        
        # Sync session state changes to job
        current_job.common_api_datasets = st.session_state.get("common_api_datasets", {}).copy()
        current_job.polymer_datasets = st.session_state.get("polymer_datasets", {}).copy()
        
        # Update job in session state
        st.session_state.jobs[st.session_state.current_job] = current_job

def show():
    st.header("Database Management")

    # Top‐level subtabs
    tab_api, tab_polymer = st.tabs(["API", "Polymers"])

    # Ensure both dataset stores exist
    for key in ("common_api_datasets", "polymer_datasets"):
        if key not in st.session_state:
            st.session_state[key] = {}

    def render_subpage(tab, session_key, tab_name):
        with tab:
            # Dataset type for saving (extract from session key)
            dataset_type = session_key.replace("_datasets", "")
            
            # ── 1st Row: Create new database ─────────────────────────────────────────
            st.subheader("Create new database")
            
            col_import, col_save = st.columns(2)
            
            # Left Column: Import external file
            with col_import:
                st.markdown("**Import external file**")
                uploaded = st.file_uploader(
                    "CSV import box",
                    type=["csv"],
                    key=f"{session_key}_new_upload"
                )
                if uploaded:
                    df = pd.read_csv(uploaded)
                    # Store temporarily for preview and saving
                    st.session_state[f"{session_key}_temp_dataset"] = df
                    st.session_state[f"{session_key}_temp_filename"] = uploaded.name
            
            # Right Column: Save database to cloud
            with col_save:
                st.markdown("**Save database to cloud**")
                
                # Dataset name input
                save_name = st.text_input(
                    "Dataset namebox:", 
                    placeholder=f"Enter name for {tab_name} dataset",
                    key=f"{session_key}_new_save_name"
                )
                
                # Save button
                save_disabled = f"{session_key}_temp_dataset" not in st.session_state
                if st.button("Save", key=f"{session_key}_new_save_btn", disabled=save_disabled):
                    if save_name.strip() and f"{session_key}_temp_dataset" in st.session_state:
                        temp_df = st.session_state[f"{session_key}_temp_dataset"]
                        
                        # Add to current session datasets
                        dataset_name = save_name.strip()
                        st.session_state[session_key][dataset_name] = temp_df
                        
                        # Save using unified storage function
                        datasets_to_save = {dataset_name: temp_df}
                        success, result = save_data_to_file(
                            datasets_to_save, 
                            "datasets", 
                            f"{dataset_type}_{dataset_name}"
                        )
                        
                        if success:
                            # COMPREHENSIVE SYNC: Save to current job for persistence
                            sync_datasets_with_current_job()
                            
                            # Clear temporary data
                            if f"{session_key}_temp_dataset" in st.session_state:
                                del st.session_state[f"{session_key}_temp_dataset"]
                            if f"{session_key}_temp_filename" in st.session_state:
                                del st.session_state[f"{session_key}_temp_filename"]
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to save: {result}")
                    elif not save_name.strip():
                        st.error("Please enter a dataset name")
                    else:
                        st.error("Please upload a CSV file first")
            
            st.divider()
            
            # ── 2nd Row: Manage existing database ─────────────────────────────────────────
            st.subheader("Manage existing database")
            
            col_load, col_summary = st.columns(2)
            
            # Left Column: Load database from cloud
            with col_load:
                st.markdown("**Load database from cloud**")
                
                # Get saved datasets using unified function
                saved_datasets = get_saved_data_list("datasets")
                # Filter for this dataset type
                filtered_datasets = [ds for ds in saved_datasets if ds["save_name"].startswith(f"{dataset_type}_")]
                
                if filtered_datasets:
                    # Create options for selectbox (toggle box of saved databases)
                    dataset_options = [""] + [f"{ds['save_name'].replace(f'{dataset_type}_', '')} ({ds['modified']})" for ds in filtered_datasets]
                    selected_saved = st.selectbox(
                        "Toggle box of saved databases:",
                        dataset_options,
                        key=f"{session_key}_load_database_select"
                    )
                    
                    if selected_saved and selected_saved != "":
                        # Extract save name from selection
                        selected_display_name = selected_saved.split(" (")[0]
                        selected_save_name = f"{dataset_type}_{selected_display_name}"
                        
                        # Find the corresponding file
                        selected_file = None
                        for ds in filtered_datasets:
                            if ds["save_name"] == selected_save_name:
                                selected_file = ds
                                break
                        
                        # Load and Remove buttons
                        col_load_btn, col_remove_btn = st.columns(2)
                        
                        with col_load_btn:
                            if st.button("📂 Load", key=f"{session_key}_load_database_btn"):
                                if selected_file:
                                    # Load using unified function
                                    loaded_datasets, saved_time, count = load_data_from_file(
                                        selected_file["filepath"], "datasets"
                                    )
                                    
                                    if loaded_datasets is not None:
                                        # Replace current datasets with loaded ones
                                        st.session_state[session_key] = loaded_datasets
                                        
                                        # COMPREHENSIVE SYNC: Save to current job for persistence
                                        sync_datasets_with_current_job()
                                        
                                        st.rerun()
                        
                        with col_remove_btn:
                            if st.button("🗑️ Remove", key=f"{session_key}_remove_database_btn"):
                                if selected_file:
                                    success, message = delete_saved_data(selected_file["filepath"])
                                    if success:
                                        st.success(f"✅ Removed database successfully")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to remove: {message}")
                else:
                    st.selectbox(
                        "Toggle box of saved databases:",
                        ["No saved databases available"],
                        disabled=True,
                        key=f"{session_key}_no_databases"
                    )
            
            # Right Column: Database Summary
            with col_summary:
                st.markdown("**Database Summary**")
                
                # Show current loaded databases in session
                if session_key in st.session_state and st.session_state[session_key]:
                    current_datasets = st.session_state[session_key]
                    
                    # Dataset selector
                    dataset_names = list(current_datasets.keys())
                    if dataset_names:
                        selected_dataset = st.selectbox(
                            "Select dataset to view:",
                            dataset_names,
                            key=f"{session_key}_summary_select"
                        )
                        
                        if selected_dataset:
                            dataset_df = current_datasets[selected_dataset]
                            st.dataframe(dataset_df, use_container_width=True)
                            st.caption(f"Shape: {dataset_df.shape[0]} rows × {dataset_df.shape[1]} columns")
                    else:
                        st.info("No datasets loaded in current session")
                else:
                    st.info("No datasets loaded in current session")
            
            st.divider()
            
            # ── 3rd Row: Save Progress and Clear Progress buttons ─────────────────────────
            st.subheader("Progress Management")
            
            col_save_progress, col_clear_progress = st.columns(2)
            
            # Get current job
            current_job_name = st.session_state.get("current_job")
            current_job = None
            if current_job_name and current_job_name in st.session_state.get("jobs", {}):
                current_job = st.session_state.jobs[current_job_name]
            
            with col_save_progress:
                st.markdown("**Save Progress**")
                if st.button("💾 Save Progress", key=f"{session_key}_save_progress", 
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
                st.markdown("**Clear Progress**")
                if st.button("🗑️ Clear Progress", key=f"{session_key}_clear_progress",
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

    # Render each subpage
    render_subpage(tab_api, "common_api_datasets", "API")
    render_subpage(tab_polymer, "polymer_datasets", "Polymers")
