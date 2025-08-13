# modules/data_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

# FIXED: Import the correct function names from storage_utils
try:
    from modules.storage_utils import (
        save_data_to_file,           
        load_data_from_file,         
        get_saved_data_list,         
        get_saved_datasets_by_type, 
        delete_saved_data,           
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
    
    # # AUTO-LOAD: Restore databases from saved files if session state is empty
    # if "databases_auto_loaded" not in st.session_state:
    #     auto_load_all_databases()
    #     st.session_state["databases_auto_loaded"] = True

# def auto_load_all_databases():
#     """Auto-load all saved databases into session state on app start/refresh"""
#     try:
#         # Load API databases
#         api_databases = get_saved_datasets_by_type("api")
#         for db_info in api_databases:
#             display_name = db_info['display_name']
#             if display_name not in st.session_state["global_api_databases"]:
#                 loaded_databases, _, _ = load_data_from_file(db_info["filepath"], "datasets")
#                 if loaded_databases:
#                     for db_name, db_data in loaded_databases.items():
#                         st.session_state["global_api_databases"][db_name] = db_data
        
#         # Load Polymer databases
#         polymer_databases = get_saved_datasets_by_type("polymer")
#         for db_info in polymer_databases:
#             display_name = db_info['display_name']
#             if display_name not in st.session_state["global_polymer_databases"]:
#                 loaded_databases, _, _ = load_data_from_file(db_info["filepath"], "datasets")
#                 if loaded_databases:
#                     for db_name, db_data in loaded_databases.items():
#                         st.session_state["global_polymer_databases"][db_name] = db_data
                        
#     except Exception as e:
#         # Silently fail auto-loading (user can manually load if needed)
#         pass

def show():
    st.header("Database Managementss")
    
    # Initialize global database storage WITH auto-loading
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
                st.markdown("**Save database**")
                
                # Dataset name input
                save_name = st.text_input(
                    "Dataset namebox:", 
                    placeholder=f"Enter name for {tab_name} database",
                    key=f"{database_type}_new_save_name"
                )
                
                # Save button - EXACT JOB MANAGEMENT PATTERN
                has_temp_dataset = f"{database_type}_temp_dataset" in st.session_state
                
                if st.button("Save", key=f"{database_type}_new_save_btn", 
                           disabled=not has_temp_dataset,
                           help="Save database to cloud"):
                    if has_temp_dataset and save_name.strip():
                        dataset_name = save_name.strip()
                        
                        # Get the dataset from session state (like job_management gets current_job)
                        temp_df = st.session_state[f"{database_type}_temp_dataset"]
                        
                        # Check if database name already exists
                        if dataset_name in st.session_state[global_db_key]:
                            st.error(f"❌ Database '{dataset_name}' already exists!")
                        else:
                            # REPLICATE JOB MANAGEMENT PATTERN EXACTLY:
                            
                            # Update session state (like job_management does)
                            st.session_state[global_db_key][dataset_name] = temp_df
                            
                            # Save using unified storage function (SAME AS JOB_MANAGEMENT)
                            database_for_saving = {dataset_name: temp_df}
                            success, result = save_data_to_file(database_for_saving, "datasets", f"{database_type}_{dataset_name}")
                            
                            if success:
                                # Clear temporary data
                                if f"{database_type}_temp_dataset" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_dataset"]
                                if f"{database_type}_temp_filename" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_filename"]
                                
                                # EXACT SAME SUCCESS MESSAGE AS JOB MANAGEMENT
                                st.success(f"✅ Database '{dataset_name}' saved successfully.")
                                st.rerun()
                            else:
                                # EXACT SAME ERROR MESSAGE AS JOB MANAGEMENT
                                st.error(f"❌ Failed to save database: {result}")
                    elif not save_name.strip():
                        st.error("Please enter a database name")
                    else:
                        st.error("❌ No dataset to save!")
            
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
                    
                    # Dataset selector
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

                # Manual Load Section (since auto-loading removed)
                st.markdown("**Load Saved Databases**")
                saved_databases = get_saved_datasets_by_type(database_type)
                
                if saved_databases:
                    if st.button(f"📂 Load All {tab_name} Databases", 
                               key=f"{database_type}_load_all_manual"):
                        loaded_count = 0
                        for ds in saved_databases:
                            display_name = ds['display_name']
                            if display_name not in st.session_state.get(global_db_key, {}):
                                loaded_databases, _, _ = load_data_from_file(ds["filepath"], "datasets")
                                if loaded_databases:
                                    for db_name, db_data in loaded_databases.items():
                                        st.session_state[global_db_key][db_name] = db_data
                                        loaded_count += 1
                        
                        if loaded_count > 0:
                            st.success(f"✅ Loaded {loaded_count} database(s)!")
                            st.rerun()
                        else:
                            st.info("All databases already loaded")
                else:
                    st.info("No saved databases found")                
                
                st.divider()
                
            
            # Right Column: Database Table Display
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

    # Render each subpage with independent database management
    render_subpage(tab_api, "api", "API")
    render_subpage(tab_polymer, "polymer", "Polymers")    
