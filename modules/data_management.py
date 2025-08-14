# modules/data_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Import the dataset_exclusive functions from storage_utils
try:
    from modules.storage_utils import (
        save_datasets_to_file,      
        load_datasets_from_file,    
        get_saved_datasets,         
        sync_datasets_with_current_job,  
        save_progress_to_job,
        clear_progress_from_job
    )
except ImportError:
    # Fallback if storage_utils not available yet
    def save_datasets_to_file(datasets, dataset_type, save_name):
        return False, "Storage utilities not available"
    def load_datasets_from_file(filepath):
        return None, "Storage utilities not available", 0
    def get_saved_datasets(dataset_type):
        return []
    def sync_datasets_with_current_job():
        pass
    def save_progress_to_job(job):
        return False, "Storage utilities not available"
    def clear_progress_from_job(job):
        return False, "Storage utilities not available"

def show():
    st.header("Database Management")

    # Top-level subtabs
    tab_api, tab_polymer = st.tabs(["API", "Polymers"])

    # Ensure both dataset stores exist - USING OLD WORKING SESSION STATE KEYS
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
                    
                    # Show preview
                    st.markdown("**Preview:**")
                    st.dataframe(df.head(), use_container_width=True)
                    st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Right Column: Save database to cloud - WORKING VERSION
            with col_save:
                st.markdown("**Save database to cloud**")
                
                # Dataset name input
                save_name = st.text_input(
                    "Dataset namebox:", 
                    placeholder=f"Enter name for {tab_name} dataset",
                    key=f"{session_key}_new_save_name"
                )
                
                # Save button - EXACT WORKING VERSION FROM OLD FILE
                save_disabled = f"{session_key}_temp_dataset" not in st.session_state
                if st.button("Save", key=f"{session_key}_new_save_btn", disabled=save_disabled):
                    if save_name.strip() and f"{session_key}_temp_dataset" in st.session_state:
                        temp_df = st.session_state[f"{session_key}_temp_dataset"]
                        
                        # Add to current session datasets
                        dataset_name = save_name.strip()
                        st.session_state[session_key][dataset_name] = temp_df
                        
                        # Also save permanently - USING WORKING FUNCTION
                        datasets_to_save = {dataset_name: temp_df}
                        success, result = save_datasets_to_file(
                            datasets_to_save, 
                            dataset_type, 
                            dataset_name
                        )
                        
                        if success:
                            # COMPREHENSIVE SYNC: Save to current job for persistence - WORKING VERSION
                            sync_datasets_with_current_job()
                            
                            # Clear temporary data
                            if f"{session_key}_temp_dataset" in st.session_state:
                                del st.session_state[f"{session_key}_temp_dataset"]
                            if f"{session_key}_temp_filename" in st.session_state:
                                del st.session_state[f"{session_key}_temp_filename"]
                            
                            st.success(f"✅ Database '{dataset_name}' saved successfully!")
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
            
            col_select, col_summary = st.columns(2)
            
            # Left Column: Database Selection
            with col_select:                
                # Load saved datasets section
                st.markdown("**Load Saved Databases**")
                saved_datasets = get_saved_datasets(dataset_type)  # USING WORKING FUNCTION
                if saved_datasets:
                    # Create options for selectbox
                    dataset_options = [""] + [f"{ds['save_name']}" for ds in saved_datasets]
                    selected_saved = st.selectbox(
                        "Select saved database:",
                        dataset_options,
                        key=f"{session_key}_load_database_select"
                    )
                    
                    if selected_saved and selected_saved != "":
                        # Extract save name from selection
                        selected_save_name = selected_saved.split(" (")[0]
                        
                        # Find the corresponding file
                        selected_file = None
                        for ds in saved_datasets:
                            if ds["save_name"] == selected_save_name:
                                selected_file = ds
                                break
                        
                        # Load and Remove buttons
                        col_load_btn, col_remove_btn = st.columns(2)
                        
                        with col_load_btn:
                            if st.button("📂 Load", key=f"{session_key}_load_database_btn"):
                                if selected_file:
                                    loaded_datasets, saved_time, count = load_datasets_from_file(selected_file["filepath"])  # USING WORKING FUNCTION
                                    
                                    if loaded_datasets is not None:
                                        # Replace current datasets with loaded ones
                                        st.session_state[session_key] = loaded_datasets
                                        
                                        # COMPREHENSIVE SYNC: Save to current job for persistence - WORKING VERSION
                                        sync_datasets_with_current_job()
                                        
                                        st.success(f"✅ Loaded {loaded_datasets} dataset")
                                        st.rerun()
                        
                        with col_remove_btn:
                            if st.button("🗑️ Remove File", key=f"{session_key}_remove_database_btn"):
                                if selected_file:
                                    try:
                                        import os
                                        os.remove(selected_file["filepath"])
                                        st.success("✅ File removed successfully")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to remove: {str(e)}")
                else:
                    st.info("No saved databases available")

            # Right Column: Database Table Display (kept in right column)
            with col_summary:
                st.markdown("**Database Table**")
                
                # Show current loaded databases in session
                if ('selected_saved' in locals() and selected_saved and 
                    session_key in st.session_state and 
                    selected_saved in st.session_state[session_key]):
                        

                    dataset_df = st.session_state[session_key][selected_saved]
                    st.dataframe(dataset_df, use_container_width=True)
                    st.caption(f"Shape: {dataset_df.shape[0]} rows × {dataset_df.shape[1]} columns")
                        
                elif session_key in st.session_state and st.session_state[session_key]:
                    st.info("Select a database from the left to view its contents")
                else:
                    st.info("No databases loaded in current session")
            
            st.divider()         

    # Render each subpage - USING OLD WORKING SESSION KEYS
    render_subpage(tab_api, "common_api_datasets", "API")
    render_subpage(tab_polymer, "polymer_datasets", "Polymers")
