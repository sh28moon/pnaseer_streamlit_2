# modules/data_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

# FIXED: Import the correct function names from storage_utils
try:
    from modules.storage_utils import (
        save_data_to_file,           # Was: save_database_to_file
        load_data_from_file,         # Was: load_database_from_file  
        get_saved_data_list,         # Was: get_saved_databases_list
        get_saved_datasets_by_type,  # ADDED: This was missing
        delete_saved_data,           # Was: delete_database_file
        save_progress_to_job,
        clear_progress_from_job
    )
except ImportError:
    # Fallback if storage_utils not available yet
    def save_data_to_file(data, data_type, save_name):
        return False, "Storage utilities not available"
    def load_data_from_file(filepath, data_type):
        return None, "Storage utilities not available", 0
    def get_saved_data_list(data_type):
        return []
    def get_saved_datasets_by_type(dataset_type):
        return []
    def delete_saved_data(filepath):
        return False, "Storage utilities not available"
    def save_progress_to_job(job):
        return False, "Storage utilities not available"
    def clear_progress_from_job(job):
        return False, "Storage utilities not available"

def initialize_global_databases():
    """Initialize global database storage independent of jobs"""
    if "global_api_databases" not in st.session_state:
        st.session_state["global_api_databases"] = {}
    if "global_polymer_databases" not in st.session_state:
        st.session_state["global_polymer_databases"] = {}

def sync_job_database_references():
    """Sync current job's database references (not ownership) - OPTIONAL"""
    current_job_name = st.session_state.get("current_job")
    if current_job_name and current_job_name in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[current_job_name]
        
        # Store references to which databases are currently "active" for this job
        # But databases exist independently in global storage
        if not hasattr(current_job, 'active_api_databases'):
            current_job.active_api_databases = []
        if not hasattr(current_job, 'active_polymer_databases'):
            current_job.active_polymer_databases = []

def show():
    st.header("Database Management")
    
    # Initialize global database storage
    initialize_global_databases()

    # Top‐level subtabs
    tab_api, tab_polymer = st.tabs(["API", "Polymers"])

    def render_subpage(tab, database_type, tab_name):
        with tab:
            # Use global database storage (not job-specific)
            global_db_key = f"global_{database_type}_databases"
            
            # ── 1st Row: Create new database ─────────────────────────────────────────
            st.subheader("Create new database")
            
            col_import, col_save = st.columns(2)
            
            # Left Column: Import external file
            with col_import:
                st.markdown("**Import external file**")
                uploaded = st.file_uploader(
                    "CSV import box",
                    type=["csv"],
                    key=f"{database_type}_new_upload"
                )
                if uploaded:
                    df = pd.read_csv(uploaded)
                    # Store temporarily for preview and saving
                    st.session_state[f"{database_type}_temp_dataset"] = df
                    st.session_state[f"{database_type}_temp_filename"] = uploaded.name
                    
                    # Show preview
                    st.markdown("**Preview:**")
                    st.dataframe(df.head(), use_container_width=True)
                    st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
# Right Column: Save database to cloud
            with col_save:
                st.markdown("**Save database to cloud**")
                
                # Dataset name input
                save_name = st.text_input(
                    "Dataset namebox:", 
                    placeholder=f"Enter name for {tab_name} database",
                    key=f"{database_type}_new_save_name"
                )
                
                # Save button - now includes progress saving functionality (same as "Save Progress")
                save_disabled = f"{database_type}_temp_dataset" not in st.session_state
                if st.button("Save", key=f"{database_type}_new_save_btn", disabled=save_disabled):
                    if save_name.strip() and f"{database_type}_temp_dataset" in st.session_state:
                        temp_df = st.session_state[f"{database_type}_temp_dataset"]
                        
                        # Check if database name already exists
                        if save_name.strip() in st.session_state[global_db_key]:
                            st.error(f"❌ Database '{save_name.strip()}' already exists!")
                        else:
                            # Add to global database storage (independent of jobs)
                            dataset_name = save_name.strip()
                            st.session_state[global_db_key][dataset_name] = temp_df
                            
                            # 1. Save individual database file
                            datasets_to_save = {dataset_name: temp_df}
                            success, result = save_data_to_file(
                                datasets_to_save, 
                                "datasets", 
                                f"{database_type}_{dataset_name}"
                            )
                            
                            # 2. Save global database progress (same function as "Save Progress" button)
                            progress_success, progress_result = save_progress_to_job(None)  # None = no job, save global state
                            
                            # Show results
                            if success:
                                # Clear temporary data
                                if f"{database_type}_temp_dataset" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_dataset"]
                                if f"{database_type}_temp_filename" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_filename"]
                                
                                st.success(f"✅ Database '{dataset_name}' saved successfully!")
                                
                                # Show progress save status (same as "Save Progress" button)
                                if progress_success:
                                    st.success(f"✅ Global database progress saved!")
                                else:
                                    st.warning(f"⚠️ Database saved but progress save failed: {progress_result}")
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to save: {result}")
                    elif not save_name.strip():
                        st.error("Please enter a database name")
                    else:
                        st.error("Please upload a CSV file first")
            
            st.divider()
            
# ── 2nd Row: Manage existing database ─────────────────────────────────────────
            st.subheader("Manage existing database")
            
            col_select, col_summary = st.columns(2)
            
            # Left Column: Database Selection (moved from right column)
            with col_select:
                st.markdown("**Select Database to View**")
                
                # Show current loaded databases in global storage
                if global_db_key in st.session_state and st.session_state[global_db_key]:
                    current_databases = st.session_state[global_db_key]
                    
                    st.markdown(f"**📂 Currently Loaded ({len(current_databases)}):**")
                    
                    # Dataset selector (moved from right column)
                    database_names = list(current_databases.keys())
                    if database_names:
                        selected_database = st.selectbox(
                            "Select database to view:",
                            database_names,
                            key=f"{database_type}_summary_select"
                        )
                        
                        # Add remove from memory button
                        if selected_database:
                            if st.button(f"🗑️ Remove '{selected_database}' from Memory", 
                                       key=f"{database_type}_remove_from_memory",
                                       help="Remove from memory only (keeps saved file)"):
                                del st.session_state[global_db_key][selected_database]
                                st.success(f"✅ Removed '{selected_database}' from memory")
                                st.rerun()
                    else:
                        selected_database = None
                        st.info("No databases loaded in memory")
                else:
                    selected_database = None
                    st.info("No databases loaded in memory")
                
                st.divider()
                
                # Show summary statistics
                total_loaded = len(st.session_state.get(global_db_key, {}))
                total_saved = len(get_saved_datasets_by_type(database_type))
                
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.metric("📂 Loaded", total_loaded, help="Currently in memory")
                with col_stat2:
                    st.metric("💾 Saved", total_saved, help="Available files")
                
                # Quick load all button if there are unloaded databases
                if total_saved > total_loaded:
                    unloaded_count = total_saved - total_loaded
                    if st.button(f"⚡ Load All Available ({unloaded_count})", 
                               key=f"{database_type}_load_all",
                               help="Load all saved databases into memory"):
                        saved_databases = get_saved_datasets_by_type(database_type)
                        loaded_count = 0
                        
                        for ds in saved_databases:
                            display_name = ds['display_name']
                            # Only load if not already loaded
                            if display_name not in st.session_state.get(global_db_key, {}):
                                loaded_databases, _, _ = load_data_from_file(ds["filepath"], "datasets")
                                if loaded_databases:
                                    for db_name, db_data in loaded_databases.items():
                                        st.session_state[global_db_key][db_name] = db_data
                                        loaded_count += 1
                        
                        if loaded_count > 0:
                            st.success(f"✅ Loaded {loaded_count} additional database(s)!")
                            st.rerun()
                        else:
                            st.info("All databases already loaded")
            
            # Right Column: Database Table Display (kept in right column)
            with col_summary:
                st.markdown("**Database Table**")
                
                # Show the selected database table
                if ('selected_database' in locals() and selected_database and 
                    global_db_key in st.session_state and 
                    selected_database in st.session_state[global_db_key]):
                    
                    database_df = st.session_state[global_db_key][selected_database]
                    st.dataframe(database_df, use_container_width=True)
                    st.caption(f"Shape: {database_df.shape[0]} rows × {database_df.shape[1]} columns")
                    
                elif global_db_key in st.session_state and st.session_state[global_db_key]:
                    st.info("Select a database from the left to view its contents")
                else:
                    st.info("No databases loaded in memory")
                
                st.divider()
                
                # Show summary statistics
                total_loaded = len(st.session_state.get(global_db_key, {}))
                total_saved = len(get_saved_datasets_by_type(database_type))
                
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.metric("📂 Loaded", total_loaded, help="Currently in memory")
                with col_stat2:
                    st.metric("💾 Saved", total_saved, help="Available files")
                
                # Quick load all button if there are unloaded databases
                if total_saved > total_loaded:
                    unloaded_count = total_saved - total_loaded
                    if st.button(f"⚡ Load All Available ({unloaded_count})", 
                               key=f"{database_type}_load_all",
                               help="Load all saved databases into memory"):
                        saved_databases = get_saved_datasets_by_type(database_type)
                        loaded_count = 0
                        
                        for ds in saved_databases:
                            display_name = ds['display_name']
                            # Only load if not already loaded
                            if display_name not in st.session_state.get(global_db_key, {}):
                                loaded_databases, _, _ = load_data_from_file(ds["filepath"], "datasets")
                                if loaded_databases:
                                    for db_name, db_data in loaded_databases.items():
                                        st.session_state[global_db_key][db_name] = db_data
                                        loaded_count += 1
                        
                        if loaded_count > 0:
                            st.success(f"✅ Loaded {loaded_count} additional database(s)!")
                            st.rerun()
                        else:
                            st.info("All databases already loaded")
            
            st.divider()            

    # Render each subpage with independent database management
    render_subpage(tab_api, "api", "API")
    render_subpage(tab_polymer, "polymer", "Polymers")
