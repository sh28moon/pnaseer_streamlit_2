# pages/data_management.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

def save_datasets_to_file(datasets, dataset_type, save_name):
    """Save datasets to JSON file"""
    try:
        # Create saved_datasets directory if it doesn't exist
        os.makedirs("saved_datasets", exist_ok=True)
        
        # Convert datasets to serializable format
        dataset_data = {}
        for name, df in datasets.items():
            if df is not None:
                dataset_data[name] = df.to_dict('records')
        
        # Create save data structure
        save_data = {
            "save_name": save_name,
            "dataset_type": dataset_type,
            "datasets": dataset_data,
            "saved_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataset_count": len(dataset_data)
        }
        
        # Save to file
        filename = f"saved_datasets/{dataset_type}_{save_name}.json"
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return True, filename
    except Exception as e:
        return False, str(e)

def load_datasets_from_file(filepath):
    """Load datasets from JSON file"""
    try:
        with open(filepath, 'r') as f:
            save_data = json.load(f)
        
        # Convert back to DataFrames
        loaded_datasets = {}
        for name, records in save_data["datasets"].items():
            loaded_datasets[name] = pd.DataFrame(records)
        
        return loaded_datasets, save_data.get("saved_timestamp", "Unknown"), save_data.get("dataset_count", 0)
    except Exception as e:
        return None, str(e), 0

def get_saved_datasets(dataset_type):
    """Get list of saved dataset files for specific type"""
    try:
        if not os.path.exists("saved_datasets"):
            return []
        
        saved_files = []
        prefix = f"{dataset_type}_"
        
        for filename in os.listdir("saved_datasets"):
            if filename.startswith(prefix) and filename.endswith(".json"):
                save_name = filename[len(prefix):-5]  # Remove prefix and .json
                filepath = f"saved_datasets/{filename}"
                # Get file modification time
                mtime = os.path.getmtime(filepath)
                saved_files.append({
                    "save_name": save_name,
                    "filename": filename,
                    "filepath": filepath,
                    "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # Sort by modification time (newest first)
        saved_files.sort(key=lambda x: x["modified"], reverse=True)
        return saved_files
    except Exception:
        return []

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
            
            # ── Load Database Section ─────────────────────────────────────────
            st.subheader("Load Database")
            
            saved_datasets = get_saved_datasets(dataset_type)
            if saved_datasets:
                col_select, col_import, col_remove = st.columns([3, 1, 1])
                
                with col_select:
                    # Create options for selectbox
                    dataset_options = [""] + [f"{ds['save_name']} ({ds['modified']})" for ds in saved_datasets]
                    selected_saved = st.selectbox(
                        f"Select saved {tab_name} database:",
                        dataset_options,
                        key=f"{session_key}_load_database_select"
                    )
                
                with col_import:
                    if selected_saved and selected_saved != "":
                        # Extract save name from selection
                        selected_save_name = selected_saved.split(" (")[0]
                        
                        # Find the corresponding file
                        selected_file = None
                        for ds in saved_datasets:
                            if ds["save_name"] == selected_save_name:
                                selected_file = ds
                                break
                        
                        if selected_file:
                            if st.button("📂 Load", key=f"{session_key}_load_database_btn"):
                                loaded_datasets, saved_time, count = load_datasets_from_file(selected_file["filepath"])
                                
                                if loaded_datasets is not None:
                                    # Replace current datasets with loaded ones
                                    st.session_state[session_key] = loaded_datasets
                                    st.success(f"✅ Loaded '{selected_save_name}' database with {count} dataset(s)!")
                                    st.rerun()
                
                with col_remove:
                    if selected_saved and selected_saved != "":
                        if st.button("🗑️ Remove", key=f"{session_key}_remove_database_btn"):
                            if selected_file:
                                try:
                                    os.remove(selected_file["filepath"])
                                    st.success(f"✅ Removed '{selected_save_name}' database")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to remove: {str(e)}")
            
            st.divider()
            
            # ── New Database Section ─────────────────────────────────────────
            st.subheader("New Database")
            
            # Upload CSV row
            st.markdown("**Upload CSV**")
            uploaded = st.file_uploader(
                "Select CSV file",
                type=["csv"],
                key=f"{session_key}_new_upload"
            )
            if uploaded:
                df = pd.read_csv(uploaded)
                # Store temporarily for preview and saving
                st.session_state[f"{session_key}_temp_dataset"] = df
                st.session_state[f"{session_key}_temp_filename"] = uploaded.name
                st.success(f"Loaded: {uploaded.name}")
            
            # Dataset Summary and Save Dataset row
            col_summary, col_save = st.columns(2)
            
            # Column 1: Dataset Summary (Table)
            with col_summary:
                st.markdown("**Dataset Summary**")
                if f"{session_key}_temp_dataset" in st.session_state:
                    temp_df = st.session_state[f"{session_key}_temp_dataset"]
                    st.dataframe(temp_df, use_container_width=True)
                    st.write(f"Shape: {temp_df.shape[0]} rows × {temp_df.shape[1]} columns")
            
            # Column 2: Save Dataset
            with col_save:
                st.markdown("**Save Dataset**")
                
                # Save name input
                save_name = st.text_input(
                    "Dataset Name:", 
                    placeholder=f"Enter name for {tab_name} dataset",
                    key=f"{session_key}_new_save_name"
                )
                
                # Save button
                save_disabled = f"{session_key}_temp_dataset" not in st.session_state
                if st.button("💾 Save Dataset", key=f"{session_key}_new_save_btn", disabled=save_disabled):
                    if save_name.strip() and f"{session_key}_temp_dataset" in st.session_state:
                        temp_df = st.session_state[f"{session_key}_temp_dataset"]
                        
                        # Add to current session datasets
                        dataset_name = save_name.strip()
                        st.session_state[session_key][dataset_name] = temp_df
                        
                        # Also save permanently
                        datasets_to_save = {dataset_name: temp_df}
                        success, result = save_datasets_to_file(
                            datasets_to_save, 
                            dataset_type, 
                            dataset_name
                        )
                        
                        if success:
                            st.success(f"✅ Saved '{dataset_name}' permanently!")
                            
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

    # Render each subpage
    render_subpage(tab_api, "common_api_datasets", "API")
    render_subpage(tab_polymer, "polymer_datasets", "Polymers")
