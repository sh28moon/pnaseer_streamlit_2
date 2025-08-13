# modules/data_management.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Import unified storage functions
try:
    from modules.storage_utils import (
        save_data_to_file, 
        load_data_from_file, 
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
                
                # Save button
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
                            
                            # Save permanently using unified storage function
                            datasets_to_save = {dataset_name: temp_df}
                            success, result = save_data_to_file(
                                datasets_to_save, 
                                "datasets", 
                                f"{database_type}_{dataset_name}"
                            )
                            
                            if success:
                                # Clear temporary data
                                if f"{database_type}_temp_dataset" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_dataset"]
                                if f"{database_type}_temp_filename" in st.session_state:
                                    del st.session_state[f"{database_type}_temp_filename"]
                                
                                st.success(f"✅ Database '{dataset_name}' saved successfully!")
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
            
            col_load, col_summary = st.columns(2)
            
            # Left Column: Load database from cloud
            with col_load:
                st.markdown("**Load database from cloud**")
                
                # Get saved databases using unified function with filtering
                saved_databases = get_saved_datasets_by_type(database_type)
                
                if saved_databases:
                    # Create options for selectbox (toggle box of saved databases)
                    database_options = [""] + [f"{ds['display_name']} ({ds['modified']})" for ds in saved_databases]
                    selected_saved = st.selectbox(
                        "Toggle box of saved databases:",
                        database_options,
                        key=f"{database_type}_load_database_select"
                    )
                    
                    if selected_saved and selected_saved != "":
                        # Extract save name from selection
                        selected_display_name = selected_saved.split(" (")[0]
                        
                        # Find the corresponding file
                        selected_file = None
                        for ds in saved_databases:
                            if ds["display_name"] == selected_display_name:
                                selected_file = ds
                                break
                        
                        # Load and Remove buttons
                        col_load_btn, col_remove_btn = st.columns(2)
                        
                        with col_load_btn:
                            if st.button("📂 Load", key=f"{database_type}_load_database_btn"):
                                if selected_file:
                                    # Load using unified function
                                    loaded_databases, saved_time, count = load_data_from_file(selected_file["filepath"], "datasets")
                                    
                                    if loaded_databases is not None:
                                        # Add to global database storage (merge, don't replace)
                                        for db_name, db_data in loaded_databases.items():
                                            st.session_state[global_db_key][db_name] = db_data
                                        
                                        st.success(f"✅ Loaded {count} database(s) successfully!")
                                        st.rerun()
                        
                        with col_remove_btn:
                            if st.button("🗑️ Remove", key=f"{database_type}_remove_database_btn"):
                                if selected_file:
                                    success, message = delete_saved_data(selected_file["filepath"])
                                    if success:
                                        st.success(f"✅ Removed database file successfully")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to remove: {message}")
                else:
                    st.selectbox(
                        "Toggle box of saved databases:",
                        ["No saved databases available"],
                        disabled=True,
                        key=f"{database_type}_no_databases"
                    )
            
            # Right Column: Database Summary
            with col_summary:
                st.markdown("**Database Summary**")
                
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
                        
                        if selected_database:
                            database_df = current_databases[selected_database]
                            st.dataframe(database_df, use_container_width=True)
                            st.caption(f"Shape: {database_df.shape[0]} rows × {database_df.shape[1]} columns")
                            
                            # Add remove from memory button
                            if st.button(f"🗑️ Remove '{selected_database}' from Memory", 
                                       key=f"{database_type}_remove_from_memory",
                                       help="Remove from memory only (keeps saved file)"):
                                del st.session_state[global_db_key][selected_database]
                                st.success(f"✅ Removed '{selected_database}' from memory")
                                st.rerun()
                    else:
                        st.info("No databases loaded in memory")
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
                if st.button("💾 Save Progress", key=f"{database_type}_save_progress", 
                           disabled=not current_job,
                           help="Save current job progress to cloud"):
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
                if st.button("🗑️ Clear Progress", key=f"{database_type}_clear_progress",
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

    # Render each subpage with independent database management
    render_subpage(tab_api, "api", "API")
    render_subpage(tab_polymer, "polymer", "Polymers")
    
    # Show global database status
    st.divider()
    st.markdown("## 📊 Global Database Status")
    
    col_api_status, col_polymer_status = st.columns(2)
    
    with col_api_status:
        api_count = len(st.session_state.get("global_api_databases", {}))
        st.metric("API Databases", api_count)
        if api_count > 0:
            api_names = list(st.session_state["global_api_databases"].keys())
            st.caption(f"Available: {', '.join(api_names[:3])}{'...' if len(api_names) > 3 else ''}")
    
    with col_polymer_status:
        polymer_count = len(st.session_state.get("global_polymer_databases", {}))
        st.metric("Polymer Databases", polymer_count)
        if polymer_count > 0:
            polymer_names = list(st.session_state["global_polymer_databases"].keys())
            st.caption(f"Available: {', '.join(polymer_names[:3])}{'...' if len(polymer_names) > 3 else ''}")
