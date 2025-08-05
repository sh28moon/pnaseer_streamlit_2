# pages/inputs.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.markdown('<p class="font-large"><b>Input Conditions</b></p>', unsafe_allow_html=True)

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    st.info(f"📁 Working on job: **{current_job_name}**")

    # Top-level tabs
    tab_api, tab_target = st.tabs(["API Properties", "Target Profile"])

    # ── API Tab ──────────────────────────────────────────────────────────────
    with tab_api:
        st.markdown('<p class="font-medium"><b>Import API dataset</b></p>', unsafe_allow_html=True)

        # Import data row
        uploaded = st.file_uploader(
            "Label",
            label_visibility="hidden",
            type=["csv"],
            key="input_api_file"
        )
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
            except Exception:
                df = pd.DataFrame()
            st.session_state["input_api_df"] = df
            st.success(f"Loaded {uploaded.name}")

        # Imported data container with toggle
        if st.session_state.get("input_api_df") is not None and not st.session_state.get("input_api_df").empty:
            with st.expander("📄 Imported API Data", expanded=False):
                df = st.session_state["input_api_df"]
                st.dataframe(df, use_container_width=True)
                st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")

        st.divider() 

        # Data summary and save section
        st.markdown("**Data Summary**")
        
        # Show current job API data if exists
        if current_job.has_api_data():
            st.dataframe(current_job.api_dataset, use_container_width=True)
            st.success("✅ API data saved to current job")
        else:
            st.info("No API data saved to current job yet.")
        
        # Save button - always show if there's temp data or existing job data
        temp_df = st.session_state.get("input_api_df", pd.DataFrame())
        if not temp_df.empty or current_job.has_api_data():
            col1, col2 = st.columns(2)
            with col1:
                button_text = "Update API Data in Job" if current_job.has_api_data() else "Save API Data to Job"
                if st.button(button_text, key="save_api_data"):
                    if not temp_df.empty:
                        current_job.api_dataset = temp_df
                        st.session_state.jobs[current_job_name] = current_job
                        action = "updated" if current_job.has_api_data() else "saved"
                        st.success(f"API data {action} in job '{current_job_name}'")
                        st.rerun()
                    else:
                        st.error("No API data to save. Please import data first.")
            
            with col2:
                # Clear API data from job
                if current_job.has_api_data():
                    if st.button("🗑️ Clear API Data", key="clear_api_data", help="Remove API data from current job"):
                        current_job.api_dataset = None
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"API data cleared from job '{current_job_name}'")
                        st.rerun()

    # ── Target Profile Tab ───────────────────────────────────────────────────
    with tab_target:
        st.markdown('<p class="font-medium"><b>Target Profile</b></p>', unsafe_allow_html=True)

        # Ensure data stores exist
        if "input_target_datasets" not in st.session_state:
            st.session_state["input_target_datasets"] = {}
            st.session_state["input_target_manual_count"] = 0

        # Main 2-column structure
        col_left, col_right = st.columns(2)

        # ── Left Column: Target Profile Input ──────────────────────────────────
        with col_left:
            st.subheader("Target Profile Input")
            
            st.markdown("**Import Data**")
            uploaded_tp = st.file_uploader(
                "Import Target Data (CSV only)",
                type=["csv"],
                key="target_profile_file"
            )
            if uploaded_tp:
                try:
                    df_tp = pd.read_csv(uploaded_tp)
                    
                    # Validate data structure
                    if 'Name' not in df_tp.columns:
                        st.error("❌ Target CSV must have a 'Name' column for dataset identification.")
                        st.error("Expected structure: [Name, Modulus, Encapsulation Rate, Release Time (Day)]")
                    elif len(df_tp.columns) < 4:
                        st.error(f"❌ Invalid file structure. Expected at least 4 columns, got {len(df_tp.columns)}.")
                        st.error("Required structure: [Name, Modulus, Encapsulation Rate, Release Time (Day)]")
                    elif len(df_tp) == 0:
                        st.error("❌ File is empty. Please upload a file with data.")
                    else:
                        # Create separate datasets for each row
                        target_datasets = {}
                        for index, row in df_tp.iterrows():
                            dataset_name = str(row['Name']).strip()
                            if dataset_name:  # Only add if name is not empty
                                # Create single-row dataframe for this dataset
                                dataset_df = pd.DataFrame([row])
                                target_datasets[dataset_name] = dataset_df
                        
                        # File structure is valid
                        if target_datasets:
                            st.session_state["temp_target_data"] = target_datasets
                            st.success(f"✅ {len(target_datasets)} target datasets loaded from '{uploaded_tp.name}'")
                            st.info(f"📊 Datasets: {', '.join(list(target_datasets.keys())[:3])}" + 
                                   (f" and {len(target_datasets)-3} more" if len(target_datasets) > 3 else ""))
                            
                            # Show column preview
                            with st.expander("📄 Preview Dataset Structure", expanded=False):
                                first_dataset = list(target_datasets.values())[0]
                                col_info = {
                                    "Column Index": list(range(len(first_dataset.columns))),
                                    "Column Name": first_dataset.columns.tolist(),
                                    "Expected": ["Name", "Modulus", "Encapsulation Rate", "Release Time (Day)"] + ["Additional"] * (len(first_dataset.columns) - 4)
                                }
                                df_preview = pd.DataFrame(col_info)
                                st.dataframe(df_preview, use_container_width=True)
                        else:
                            st.error("❌ No valid datasets found. Check that Name column contains values.")
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
                    st.error("Please ensure the file is a valid CSV format.")
                    
            # Save imported data to job button
            if st.session_state.get("temp_target_data"):
                if st.button("💾 Save Imported Data to Job", key="save_imported_to_job"):
                    temp_data = st.session_state["temp_target_data"]
                    if current_job.has_target_data():
                        current_job.target_profile_dataset.update(temp_data)
                    else:
                        current_job.target_profile_dataset = temp_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"{len(temp_data)} imported dataset(s) saved to job '{current_job_name}'")
                    st.rerun()

            st.divider()
            
            st.markdown("**Manual Input**")
            
            # Dataset name input
            dataset_name = st.text_input("Dataset Name", placeholder="Enter dataset name", key="manual_dataset_name")
            
            # Parameter inputs
            modulus = st.number_input("Modulus", min_value=0.0, format="%.2f", key="tp_modulus")
            encapsulation_rate = st.number_input("Encapsulation Rate", min_value=0.0, format="%.2f", key="tp_encapsulation_rate")
            release_time = st.number_input("Release Time (Day)", min_value=0.0, format="%.2f", key="tp_release_time")

            # Single button to add and save directly to job
            if st.button("💾 Add to Job", key="add_manual_to_job"):
                if not dataset_name.strip():
                    st.error("Please enter a dataset name.")
                else:
                    # Create manual input dataset with 4 columns including name
                    df_manual = pd.DataFrame([{
                        "Name": dataset_name.strip(),
                        "Modulus": modulus,
                        "Encapsulation Rate": encapsulation_rate,
                        "Release Time (Day)": release_time
                    }])
                    
                    # Save directly to job using the dataset name as key
                    if current_job.has_target_data():
                        current_job.target_profile_dataset[dataset_name.strip()] = df_manual
                    else:
                        current_job.target_profile_dataset = {dataset_name.strip(): df_manual}
                    
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Dataset '{dataset_name.strip()}' added to job '{current_job_name}'")
                    st.rerun()

            st.divider()
            
            # Global clear button
            if current_job.has_target_data():
                if st.button("🗑️ Clear All Target Data from Job", key="clear_all_target_data", help="Remove all target data from current job"):
                    current_job.target_profile_dataset = None
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"All target data cleared from job '{current_job_name}'")
                    st.rerun()

        # ── Right Column: Input Summary ──────────────────────────────────────
        with col_right:
            st.subheader("Input Summary")
            
            # Only show data from current job (no temporary datasets)
            if current_job.has_target_data():
                st.success("✅ Target data saved to current job")
                job_data = current_job.target_profile_dataset
                
                selected = st.selectbox(
                    "Select Dataset from Job",
                    list(job_data.keys()),
                    key="job_target_select"
                )
                
                # Remove dataset button
                if st.button(f"🗑️ Remove '{selected}' from Job", key="remove_selected_dataset", help=f"Remove {selected} from current job"):
                    # Remove the selected dataset from job
                    if selected in current_job.target_profile_dataset:
                        del current_job.target_profile_dataset[selected]
                        # If no datasets left, set to None
                        if not current_job.target_profile_dataset:
                            current_job.target_profile_dataset = None
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Dataset '{selected}' removed from job '{current_job_name}'")
                        st.rerun()
                
                df_sel = job_data[selected]
                
                # Show table
                st.markdown("**Data Table**")
                st.dataframe(df_sel, use_container_width=True)

                # Show radar chart for job data
                if len(df_sel.columns) >= 4:  # Check if we have enough columns (name + 3 data columns)
                    # Skip first column (profile names) and get the 3 data columns
                    data_columns = df_sel.columns[1:4]  # Get columns 1, 2, 3 (skip column 0)
                    
                    if len(data_columns) >= 3:
                        vals = df_sel.iloc[0][data_columns].tolist()
                        labels = ["Modulus", "Encapsulation Rate", "Release Time (Day)"]
                        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                        vals += vals[:1]
                        angles += angles[:1]

                        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                        ax.plot(angles, vals, marker="o", linewidth=2)
                        ax.fill(angles, vals, alpha=0.25)
                        ax.set_thetagrids(np.degrees(angles), labels + [labels[0]])
                        ax.set_ylim(0, max(1.0, max(vals)))
                        ax.set_title(f"Target Profile: {selected}", y=1.1)
                        st.pyplot(fig)
                    else:
                        st.warning("Insufficient data columns for radar chart")
                else:
                    st.warning("Dataset needs at least 4 columns (name + 3 data values) for radar chart")
            else:
                st.info("No target datasets in current job. Import data or add manual input to get started.")