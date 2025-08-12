# pages/inputs.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.markdown('<p class="font-large"><b>Manage Target Profile</b></p>', unsafe_allow_html=True)

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]

    # Two main tabs
    tab_create, tab_summary = st.tabs(["Create New Profile", "Target Profile Summary"])

    # ── Create New Profile Tab ───────────────────────────────────────────
    with tab_create:
        # Ensure database stores exist
        for key in ("common_api_datasets", "polymer_datasets"):
            if key not in st.session_state:
                st.session_state[key] = {}

        # Initialize temporary storage for profile creation
        if "temp_profile_creation" not in st.session_state:
            st.session_state.temp_profile_creation = {
                "api_data": None,
                "api_name": None,
                "polymer_data": None,
                "polymer_name": None,
                "formulation_data": None
            }

        # ── 1st Row: Select API from database ─────────────────────────────────
        st.subheader("Select API from database")
        
        if st.session_state.get("common_api_datasets"):
            api_datasets = st.session_state["common_api_datasets"]
            api_dataset_options = [""] + list(api_datasets.keys())
            
            col_dataset, col_row, col_save = st.columns([2, 2, 1])
            
            with col_dataset:
                selected_api_dataset = st.selectbox(
                    "Select API Dataset:",
                    api_dataset_options,
                    key="create_api_dataset_select"
                )
            
            with col_row:
                if selected_api_dataset:
                    dataset_df = api_datasets[selected_api_dataset]
                    
                    if len(dataset_df) > 1:
                        if 'Name' in dataset_df.columns:
                            row_options = []
                            for idx, row in dataset_df.iterrows():
                                name = row['Name'] if pd.notna(row['Name']) else f"Row {idx + 1}"
                                row_options.append(f"{name} (Row {idx + 1})")
                            
                            selected_row_option = st.selectbox(
                                "Select API:",
                                row_options,
                                key="create_api_row_select"
                            )
                            
                            selected_row_index = int(selected_row_option.split("(Row ")[1].split(")")[0]) - 1
                            selected_api_data = dataset_df.iloc[[selected_row_index]].copy()
                        else:
                            row_numbers = [f"Row {i+1}" for i in range(len(dataset_df))]
                            selected_row_display = st.selectbox(
                                "Select API:",
                                row_numbers,
                                key="create_api_row_select"
                            )
                            selected_row_index = row_numbers.index(selected_row_display)
                            selected_api_data = dataset_df.iloc[[selected_row_index]].copy()
                    else:
                        selected_api_data = dataset_df.copy()
                        st.selectbox("Select API:", ["Single API (auto-selected)"], disabled=True, key="api_single")
                else:
                    selected_api_data = None
                    st.selectbox("Select API:", ["Select dataset first"], disabled=True, key="api_placeholder")
            
            with col_save:
                st.write("")  # Space for alignment
                if st.button("💾 Save API", key="save_api_to_temp"):
                    if selected_api_data is not None:
                        st.session_state.temp_profile_creation["api_data"] = selected_api_data
                        # Save API name for display
                        api_name = selected_api_data['Name'].iloc[0] if 'Name' in selected_api_data.columns else "Unnamed API"
                        st.session_state.temp_profile_creation["api_name"] = api_name
                        st.success("API saved to profile!")
                    else:
                        st.error("Please select API data first.")
        else:
            st.warning("⚠️ No API datasets available. Please import datasets in Database Management first.")

        st.divider()

        # ── 2nd Row: Select Gel Polymer from database ────────────────────────
        st.subheader("Select Gel Polymer from database")
        
        if st.session_state.get("polymer_datasets"):
            polymer_datasets = st.session_state["polymer_datasets"]
            polymer_dataset_options = [""] + list(polymer_datasets.keys())
            
            col_dataset, col_row, col_save = st.columns([2, 2, 1])
            
            with col_dataset:
                selected_polymer_dataset = st.selectbox(
                    "Select Polymer Dataset:",
                    polymer_dataset_options,
                    key="create_polymer_dataset_select"
                )
            
            with col_row:
                if selected_polymer_dataset:
                    dataset_df = polymer_datasets[selected_polymer_dataset]
                    
                    if len(dataset_df) > 1:
                        if 'Name' in dataset_df.columns:
                            row_options = []
                            for idx, row in dataset_df.iterrows():
                                name = row['Name'] if pd.notna(row['Name']) else f"Row {idx + 1}"
                                row_options.append(f"{name} (Row {idx + 1})")
                            
                            selected_row_option = st.selectbox(
                                "Select Polymer:",
                                row_options,
                                key="create_polymer_row_select"
                            )
                            
                            selected_row_index = int(selected_row_option.split("(Row ")[1].split(")")[0]) - 1
                            selected_polymer_data = dataset_df.iloc[[selected_row_index]].copy()
                        else:
                            row_numbers = [f"Row {i+1}" for i in range(len(dataset_df))]
                            selected_row_display = st.selectbox(
                                "Select Polymer:",
                                row_numbers,
                                key="create_polymer_row_select"
                            )
                            selected_row_index = row_numbers.index(selected_row_display)
                            selected_polymer_data = dataset_df.iloc[[selected_row_index]].copy()
                    else:
                        selected_polymer_data = dataset_df.copy()
                        st.selectbox("Select Polymer:", ["Single Polymer (auto-selected)"], disabled=True, key="polymer_single")
                else:
                    selected_polymer_data = None
                    st.selectbox("Select Polymer:", ["Select dataset first"], disabled=True, key="polymer_placeholder")
            
            with col_save:
                st.write("")  # Space for alignment
                if st.button("💾 Save Polymer", key="save_polymer_to_temp"):
                    if selected_polymer_data is not None:
                        st.session_state.temp_profile_creation["polymer_data"] = selected_polymer_data
                        # Save Polymer name for display
                        polymer_name = selected_polymer_data['Name'].iloc[0] if 'Name' in selected_polymer_data.columns else "Unnamed Polymer"
                        st.session_state.temp_profile_creation["polymer_name"] = polymer_name
                        st.success("Polymer saved to profile!")
                    else:
                        st.error("Please select polymer data first.")
        else:
            st.warning("⚠️ No Polymer datasets available. Please import datasets in Database Management first.")

        st.divider()

        # ── 3rd Row: Create Formulation Profile ──────────────────────────────
        st.subheader("Create Formulation Profile")
        
        col_import, col_manual = st.columns(2)

        # Left Column: Import CSV file
        with col_import:
            st.markdown("**Import CSV file**")
            
            uploaded_formulation = st.file_uploader(
                "Import Formulation CSV",
                type=["csv"],
                key="formulation_csv_file"
            )
            if uploaded_formulation:
                try:
                    df_formulation = pd.read_csv(uploaded_formulation)
                    
                    # Validate data structure
                    if 'Name' not in df_formulation.columns:
                        st.error("❌ CSV must have a 'Name' column.")
                    elif len(df_formulation) == 0:
                        st.error("❌ File is empty.")
                    else:
                        # Save all rows from CSV file
                        # st.success(f"✅ {len(df_formulation)} formulations loaded")
                        st.dataframe(df_formulation, use_container_width=True)
                        
                        if st.button("💾 Save Imported Formulations", key="save_imported_formulations_temp"):
                            st.session_state.temp_profile_creation["formulation_data"] = df_formulation
                            st.success(f"All {len(df_formulation)} formulations saved to profile!")
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")

        # Right Column: Manual Input
        with col_manual:
            st.markdown("**Manual Input**")
            
            # Two-column layout for input fields
            col_left, col_right = st.columns(2)
            
            with col_left:
                formulation_name = st.text_input("Name", placeholder="Formulation name", key="manual_form_name")
                modulus = st.number_input("Modulus[MPa]", min_value=0.0, format="%.2f", key="manual_form_modulus")
                release_time = st.number_input("Release Time[Week]", min_value=0.0, format="%.2f", key="manual_form_release_time")
            
            with col_right:
                dataset_type = st.text_input("Type", placeholder="e.g., Gel, Powder", key="manual_form_type")
                encapsulation_ratio = st.number_input("Encapsulation Ratio(0~1)", min_value=0.0, max_value=1.0, format="%.2f", key="manual_form_encap")

            # Save manual formulation button
            if st.button("💾 Add Manual Formulation", key="add_manual_formulation_temp"):
                if not formulation_name.strip():
                    st.error("Please enter a formulation name.")
                elif not dataset_type.strip():
                    st.error("Please enter a product type.")
                else:
                    # Create new formulation row
                    new_formulation = pd.DataFrame([{
                        "Name": formulation_name.strip(),
                        "Modulus": modulus,
                        "Encapsulation Ratio": encapsulation_ratio,
                        "Release Time (Week)": release_time,
                        "Type": dataset_type.strip()
                    }])
                    
                    # Append to existing formulation data or create new
                    if st.session_state.temp_profile_creation["formulation_data"] is not None:
                        # Append to existing data
                        existing_data = st.session_state.temp_profile_creation["formulation_data"]
                        combined_data = pd.concat([existing_data, new_formulation], ignore_index=True)
                        st.session_state.temp_profile_creation["formulation_data"] = combined_data
                        st.success(f"Manual formulation added! Total formulations: {len(combined_data)}")
                    else:
                        # Create new formulation data
                        st.session_state.temp_profile_creation["formulation_data"] = new_formulation
                        st.success("Manual formulation saved to profile!")

        st.divider()

        # ── 4th Row: Create Complete Target Profile ───────────────────────────
        st.subheader("Create Complete Target Profile")
        
        # Check if all components are ready
        temp_profile = st.session_state.temp_profile_creation
        has_api = temp_profile["api_data"] is not None
        has_polymer = temp_profile["polymer_data"] is not None
        has_formulation = temp_profile["formulation_data"] is not None
        
        col_status, col_create = st.columns([2, 1])
        
        with col_status:
            st.markdown("**Profile Status:**")
            
            # Show API name or status
            if has_api:
                api_name = temp_profile.get("api_name", "Unknown API")
                st.write(f"• API Data: {api_name}")
            else:
                st.write("• API Data: Not selected")
            
            # Show Polymer name or status
            if has_polymer:
                polymer_name = temp_profile.get("polymer_name", "Unknown Polymer")
                st.write(f"• Polymer Data: {polymer_name}")
            else:
                st.write("• Polymer Data: Not selected")
            
            # Show number of formulation rows or status
            if has_formulation:
                formulation_count = len(temp_profile["formulation_data"])
                st.write(f"• Formulation Data: {formulation_count} formulation profile")
            else:
                st.write("• Formulation Data: Not created")
        
        with col_create:
            if has_api and has_polymer and has_formulation:
                profile_name = st.text_input("Profile Name", placeholder="Enter target profile name", key="complete_profile_name")
                
                if st.button("💾 Save profile", key="save_complete_profile"):
                    if not profile_name.strip():
                        st.error("Please enter a profile name.")
                    else:
                        # Initialize complete_target_profiles if it doesn't exist
                        if not hasattr(current_job, 'complete_target_profiles'):
                            current_job.complete_target_profiles = {}
                        
                        # Check if profile name already exists
                        if profile_name.strip() in current_job.complete_target_profiles:
                            st.error(f"Profile '{profile_name.strip()}' already exists.")
                        else:
                            # Create complete target profile
                            complete_profile = {
                                "api_data": temp_profile["api_data"].copy(),
                                "polymer_data": temp_profile["polymer_data"].copy(),
                                "formulation_data": temp_profile["formulation_data"].copy(),
                                "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            current_job.complete_target_profiles[profile_name.strip()] = complete_profile
                            st.session_state.jobs[current_job_name] = current_job
                            
                            # Clear temporary data
                            st.session_state.temp_profile_creation = {
                                "api_data": None,
                                "api_name": None,
                                "polymer_data": None,
                                "polymer_name": None,
                                "formulation_data": None
                            }
                            
                            st.success(f"✅ Complete target profile '{profile_name.strip()}' saved to cloud!")
                            st.rerun()
            else:
                st.warning("Complete all three components above to create target profile.")

    # ── Target Profile Summary Tab ────────────────────────────────────────
    with tab_summary:
        # ── 1st Row: Select profile name (via togglebox) ──────────────────────
        st.subheader("Select profile name")
        
        if hasattr(current_job, 'complete_target_profiles') and current_job.complete_target_profiles:
            profile_names = list(current_job.complete_target_profiles.keys())
            selected_profile_name = st.selectbox(
                "Profile togglebox:",
                [""] + profile_names,
                key="summary_profile_select"
            )
            
            if selected_profile_name:
                selected_profile = current_job.complete_target_profiles[selected_profile_name]
                
                st.divider()
                
                # ── 2nd Row: Show API Property (table) ────────────────────────────
                st.subheader("API Property")
                if 'api_data' in selected_profile and selected_profile['api_data'] is not None:
                    st.dataframe(selected_profile['api_data'], use_container_width=True)
                else:
                    st.warning("No API data in this profile")
                
                st.divider()
                
                # ── 3rd Row: Show Gel Polymer Property (table) ───────────────────
                st.subheader("Gel Polymer Property")
                if 'polymer_data' in selected_profile and selected_profile['polymer_data'] is not None:
                    st.dataframe(selected_profile['polymer_data'], use_container_width=True)
                else:
                    st.warning("No Polymer data in this profile")
                
                st.divider()
                
                # ── 4th Row: Formulation ──────────────────────────────────────────
                st.subheader("Formulation")

                # Property Table
                if 'formulation_data' in selected_profile and selected_profile['formulation_data'] is not None:
                    st.markdown("**Property Table**")
                    st.dataframe(selected_profile['formulation_data'], use_container_width=True)
                else:
                    st.info("No formulation properties to display")

        else:
            st.info("No complete target profiles found. Create profiles in 'Create New Profile' tab.")

