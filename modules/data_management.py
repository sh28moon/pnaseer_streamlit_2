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
            
            # ── Import & Select Section ──────────────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Import Dataset")
                uploaded = st.file_uploader(
                    "Upload CSV",
                    type=["csv"],
                    key=f"{session_key}_import"
                )
                if uploaded:
                    df = pd.read_csv(uploaded)
                    st.session_state[session_key][uploaded.name] = df
                    st.success(f"Loaded dataset: {uploaded.name}")

            with col2:
                st.subheader("Select Dataset")
                names = list(st.session_state[session_key].keys())
                if names:
                    selected = st.selectbox(
                        "Choose dataset",
                        names,
                        key=f"{session_key}_select"
                    )
                else:
                    st.info("No datasets imported yet.")
                    return  # nothing more to show

            # ── Dataset Summary & Operations Section ────────────────────────
            col3, col4 = st.columns([2, 2])
            with col3:
                st.subheader("Dataset Summary")
                df_sel = st.session_state[session_key][selected]
                st.dataframe(df_sel, use_container_width=True)

            with col4:
                st.subheader("Edit & Save")
                
                # a) Add External Data
                ext = st.file_uploader(
                    "Add External Data (CSV)",
                    type=["csv"],
                    key=f"{session_key}_ext"
                )
                if ext:
                    df_ext = pd.read_csv(ext)
                    df_cur = st.session_state[session_key][selected]
                    df_new = pd.concat([df_cur, df_ext], ignore_index=True)
                    st.session_state[session_key][selected] = df_new
                    st.success("External data appended.")

                # b) Persistent Save Data
                save_name = st.text_input(
                    "Save Name:", 
                    placeholder=f"Enter name to save {tab_name} dataset",
                    key=f"{session_key}_save_name"
                )
                
                if st.button("💾 Save Dataset Permanently", key=f"{session_key}_save"):
                    if save_name.strip():
                        # Create single dataset collection for persistent save
                        datasets_to_save = {selected: st.session_state[session_key][selected]}
                        success, result = save_datasets_to_file(
                            datasets_to_save, 
                            dataset_type, 
                            save_name.strip()
                        )
                        
                        if success:
                            st.success(f"✅ Saved '{save_name}' with dataset '{selected}'!")
                            st.info(f"📁 Saved to: {result}")
                        else:
                            st.error(f"❌ Failed to save: {result}")
                    else:
                        st.error("Please enter a save name")

                # c) Remove dataset
                if st.button("🗑️ Remove Dataset", key=f"{session_key}_remove"):
                    st.session_state[session_key].pop(selected, None)
                    st.success(f"Removed Dataset: {selected}")
                    st.rerun()
            
            st.divider()
            
            # ── Load Saved Datasets Section ─────────────────────────────────
            st.subheader("Load Saved Datasets")
            
            saved_datasets = get_saved_datasets(dataset_type)
            if saved_datasets:
                col_load_select, col_load_actions = st.columns([2, 1])
                
                with col_load_select:
                    # Create options for selectbox
                    dataset_options = [""] + [f"{ds['save_name']} ({ds['modified']})" for ds in saved_datasets]
                    selected_saved = st.selectbox(
                        "Select saved dataset:",
                        dataset_options,
                        key=f"{session_key}_load_select"
                    )
                
                with col_load_actions:
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
                            if st.button("📂 Load", key=f"{session_key}_load_btn"):
                                loaded_datasets, saved_time, count = load_datasets_from_file(selected_file["filepath"])
                                
                                if loaded_datasets is not None:
                                    # Merge loaded datasets into current session
                                    st.session_state[session_key].update(loaded_datasets)
                                    st.success(f"✅ Loaded '{selected_save_name}' with {count} dataset(s)!")
                                    st.info(f"📅 Originally saved: {saved_time}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to load: {saved_time}")
                            
                            if st.button("🗑️ Delete", key=f"{session_key}_delete_btn"):
                                try:
                                    os.remove(selected_file["filepath"])
                                    st.success(f"✅ Deleted '{selected_save_name}'")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to delete: {str(e)}")
                
                # Show saved datasets info
                with st.expander(f"📋 Saved Collections ({len(saved_datasets)})", expanded=False):
                    for ds in saved_datasets[:5]:  # Show first 5
                        st.write(f"• **{ds['save_name']}**")
                        st.write(f"  📅 {ds['modified']}")
                    if len(saved_datasets) > 5:
                        st.write(f"... and {len(saved_datasets) - 5} more")
            else:
                st.info("No saved dataset collections found")

    # Render each subpage
    render_subpage(tab_api, "common_api_datasets", "API")
    render_subpage(tab_polymer, "polymer_datasets", "Polymers")
