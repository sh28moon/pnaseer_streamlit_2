# pages/inputs.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.markdown('<p class="font-large"><b>Manage target profile</b></p>', unsafe_allow_html=True)

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    st.info(f"📁 Working on job: **{current_job_name}**")

    # Two main tabs - Create target profile and Summary
    tab_create, tab_summary = st.tabs(["Create target profile", "Summary"])

    # ── Create target profile Tab ───────────────────────────────────────────
    with tab_create:
        # Ensure database stores exist
        for key in ("common_api_datasets", "polymer_datasets"):
            if key not in st.session_state:
                st.session_state[key] = {}

        # Row 1: API import
        st.markdown('<p class="font-medium"><b>API import</b></p>', unsafe_allow_html=True)
        
        # API dataset selection
        available_api_datasets = list(st.session_state.get("common_api_datasets", {}).keys())
        
        if available_api_datasets:
            col_select, col_row, col_save = st.columns([2, 2, 1])
            
            with col_select:
                selected_api_dataset = st.selectbox(
                    "Select API Dataset:",
                    available_api_datasets,
                    key="create_api_dataset_select"
                )
            
            with col_row:
                selected_api_data = None
                selected_api_name = None
                
                if selected_api_dataset:
                    dataset_df = st.session_state["common_api_datasets"][selected_api_dataset]
                    
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
                            selected_api_name = dataset_df.iloc[selected_row_index]['Name']
                        else:
                            row_numbers = [f"Row {i+1}" for i in range(len(dataset_df))]
                            selected_row_display = st.selectbox(
                                "Select API:",
                                row_numbers,
                                key="create_api_row_select"
                            )
                            selected_row_index = row_numbers.index(selected_row_display)
                            selected_api_data = dataset_df.iloc[[selected_row_index]].copy()
                            selected_api_name = selected_row_display
                    else:
                        selected_api_data = dataset_df.copy()
                        selected_api_name = dataset_df['Name'].iloc[0] if 'Name' in dataset_df.columns else "Row 1"
                        st.info("Single API available - automatically selected")
            
            with col_save:
                st.write("")  # Space for alignment
                if st.button("💾 Save API", key="save_api_data"):
                    if selected_api_data is not None:
                        current_job.api_dataset = selected_api_data
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"API '{selected_api_name}' saved!")
                        st.rerun()
                    else:
                        st.error("Please select API data first.")
        else:
            st.warning("⚠️ No API datasets available. Please import datasets in Database Management first.")
        
        st.divider()

        # Row 2: Hydrogel Polymer import
        st.markdown('<p class="font-medium"><b>Hydrogel Polymer import</b></p>', unsafe_allow_html=True)
        
        # Polymer dataset selection
        available_polymer_datasets = list(st.session_state.get("polymer_datasets", {}).keys())
        
        if available_polymer_datasets:
            col_select, col_row, col_save = st.columns([2, 2, 1])
            
            with col_select:
                selected_polymer_dataset = st.selectbox(
                    "Select Polymer Dataset:",
                    available_polymer_datasets,
                    key="create_polymer_dataset_select"
                )
            
            with col_row:
                selected_polymer_data = None
                selected_polymer_name = None
                
                if selected_polymer_dataset:
                    dataset_df = st.session_state["polymer_datasets"][selected_polymer_dataset]
                    
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
                            selected_polymer_name = dataset_df.iloc[selected_row_index]['Name']
                        else:
                            row_numbers = [f"Row {i+1}" for i in range(len(dataset_df))]
                            selected_row_display = st.selectbox(
                                "Select Polymer:",
                                row_numbers,
                                key="create_polymer_row_select"
                            )
                            selected_row_index = row_numbers.index(selected_row_display)
                            selected_polymer_data = dataset_df.iloc[[selected_row_index]].copy()
                            selected_polymer_name = selected_row_display
                    else:
                        selected_polymer_data = dataset_df.copy()
                        selected_polymer_name = dataset_df['Name'].iloc[0] if 'Name' in dataset_df.columns else "Row 1"
                        st.info("Single Polymer available - automatically selected")
            
            with col_save:
                st.write("")  # Space for alignment
                if st.button("💾 Save Polymer", key="save_polymer_data"):
                    if selected_polymer_data is not None:
                        # Store polymer data in job (reusing api_dataset field for now, or we could add a new field)
                        # For now, let's add a new attribute to store polymer data
                        if not hasattr(current_job, 'polymer_dataset'):
                            current_job.polymer_dataset = None
                        current_job.polymer_dataset = selected_polymer_data
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Polymer '{selected_polymer_name}' saved!")
                        st.rerun()
                    else:
                        st.error("Please select polymer data first.")
        else:
            st.warning("⚠️ No Polymer datasets available. Please import datasets in Database Management first.")
        
        st.divider()

        # Row 3: Formulation import
        st.markdown('<p class="font-medium"><b>Formulation import</b></p>', unsafe_allow_html=True)
        
        # Two-column layout for formulation: Import Data and Manual Input
        col_import, col_manual = st.columns(2)

        # Left Column: Import Data
        with col_import:
            st.markdown("**Import Data**")
            
            uploaded_formulation = st.file_uploader(
                "Import Formulation (CSV file with Name, Modulus, Encapsulation Rate, Release Time, Gel Polymer, Type columns)",
                type=["csv"],
                key="formulation_file"
            )
            if uploaded_formulation:
                try:
                    df_formulation = pd.read_csv(uploaded_formulation)
                    
                    # Validate data structure
                    if 'Name' not in df_formulation.columns:
                        st.error("❌ Formulation CSV must have a 'Name' column for dataset identification.")
                    elif 'Type' not in df_formulation.columns:
                        st.error("❌ Formulation CSV must have a 'Type' column for categorization.")
                    elif len(df_formulation.columns) < 6:
                        st.error(f"❌ Invalid file structure. Expected at least 6 columns (Name, Modulus, Encapsulation Ratio, Release Time, Gel Polymer, Type), got {len(df_formulation.columns)}.")
                    elif len(df_formulation) == 0:
                        st.error("❌ File is empty. Please upload a file with data.")
                    else:
                        # Create separate datasets for each row
                        formulation_datasets = {}
                        for index, row in df_formulation.iterrows():
                            dataset_name = str(row['Name']).strip()
                            if dataset_name:  # Only add if name is not empty
                                # Create single-row dataframe for this dataset
                                dataset_df = pd.DataFrame([row])
                                formulation_datasets[dataset_name] = dataset_df
                        
                        # File structure is valid
                        if formulation_datasets:
                            st.session_state["temp_formulation_data"] = formulation_datasets
                            st.success(f"✅ {len(formulation_datasets)} formulation datasets loaded")
                        else:
                            st.error("❌ No valid datasets found. Check that Name column contains values.")
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
                    
            # Save imported data to job button
            if st.session_state.get("temp_formulation_data"):
                if st.button("💾 Save Imported Data", key="save_imported_formulation"):
                    temp_data = st.session_state["temp_formulation_data"]
                    if current_job.has_target_data():
                        current_job.target_profile_dataset.update(temp_data)
                    else:
                        current_job.target_profile_dataset = temp_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"{len(temp_data)} formulation dataset(s) saved to job")
                    st.rerun()

        # Right Column: Manual Input
        with col_manual:
            st.markdown("**Manual Input**")
            
            # Profile name input
            dataset_name = st.text_input("Profile Name", placeholder="Enter profile name", key="manual_formulation_name")
            
            # Type input
            dataset_type = st.text_input("Type", placeholder="Enter desired product types (e.g., Gel, Powder)", key="manual_formulation_type")
            
            # Parameter inputs
            modulus = st.number_input("Modulus[MPa]", min_value=0.0, format="%.2f", key="formulation_modulus")
            encapsulation_ratio = st.number_input("Encapsulation Ratio(0 ~ 1)", min_value=0.0, format="%.2f", key="formulation_encapsulation_ratio")
            release_time = st.number_input("Release Time[Week]", min_value=0.0, format="%.2f", key="formulation_release_time")
            
            # Gel Polymer selection from database
            st.markdown("**Gel Polymer**")
            if "polymer_datasets" in st.session_state and st.session_state["polymer_datasets"]:
                # Collect all polymer names from all datasets
                available_polymers = []
                for dataset_name_db, dataset_df in st.session_state["polymer_datasets"].items():
                    if 'Name' in dataset_df.columns:
                        polymer_names = dataset_df['Name'].tolist()
                        available_polymers.extend([str(name) for name in polymer_names if pd.notna(name)])
                
                # Remove duplicates and sort
                unique_polymers = sorted(list(set(available_polymers)))
                
                if unique_polymers:
                    gel_polymer = st.selectbox(
                        "Select Gel Polymer:",
                        [""] + unique_polymers,
                        key="formulation_gel_polymer_select"
                    )
                else:
                    st.info("No polymers available. Import polymers in Database Management first.")
                    gel_polymer = ""
            else:
                st.info("No polymer database found. Import polymers in Database Management first.")
                gel_polymer = ""

            # Save manual formulation button
            if st.button("💾 Save Manual Data", key="save_manual_formulation"):
                if not dataset_name.strip():
                    st.error("Please enter a profile name.")
                elif not dataset_type.strip():
                    st.error("Please enter a product type.")
                elif not gel_polymer:
                    st.error("Please select a gel polymer.")
                else:
                    # Create manual input dataset with 6 columns including name, gel polymer, and type
                    df_manual = pd.DataFrame([{
                        "Name": dataset_name.strip(),
                        "Modulus": modulus,
                        "Encapsulation Ratio": encapsulation_ratio,
                        "Release Time (Day)": release_time,
                        "Gel Polymer": gel_polymer,
                        "Type": dataset_type.strip()
                    }])
                    
                    # Save directly to job using the dataset name as key
                    if current_job.has_target_data():
                        current_job.target_profile_dataset[dataset_name.strip()] = df_manual
                    else:
                        current_job.target_profile_dataset = {dataset_name.strip(): df_manual}
                    
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Formulation '{dataset_name.strip()}' added to job")
                    st.rerun()

    # ── Summary Tab ─────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Data Summary")
        
        # API Table
        st.markdown("### API")
        if current_job.has_api_data():
            api_data = current_job.api_dataset
            
            # Show API name if available
            if 'Name' in api_data.columns:
                api_name = api_data['Name'].iloc[0] if pd.notna(api_data['Name'].iloc[0]) else "Unnamed API"
                st.markdown(f"**Selected API:** {api_name}")
            
            st.dataframe(api_data, use_container_width=True)
            
            # Clear API button
            if st.button("🗑️ Clear API Data", key="clear_api_summary"):
                current_job.api_dataset = None
                st.session_state.jobs[current_job_name] = current_job
                st.success("API data cleared from job")
                st.rerun()
        else:
            st.info("No API data saved in current job. Import API data in 'Create target profile' tab.")
        
        st.divider()

        # Polymer Table
        st.markdown("### Hydrogel Polymer")
        if hasattr(current_job, 'polymer_dataset') and current_job.polymer_dataset is not None:
            polymer_data = current_job.polymer_dataset
            
            # Show Polymer name if available
            if 'Name' in polymer_data.columns:
                polymer_name = polymer_data['Name'].iloc[0] if pd.notna(polymer_data['Name'].iloc[0]) else "Unnamed Polymer"
                st.markdown(f"**Selected Polymer:** {polymer_name}")
            
            st.dataframe(polymer_data, use_container_width=True)
            
            # Clear Polymer button
            if st.button("🗑️ Clear Polymer Data", key="clear_polymer_summary"):
                current_job.polymer_dataset = None
                st.session_state.jobs[current_job_name] = current_job
                st.success("Polymer data cleared from job")
                st.rerun()
        else:
            st.info("No Hydrogel Polymer data saved in current job. Import Polymer data in 'Create target profile' tab.")
        
        st.divider()

        # Formulation Table
        st.markdown("### Formulation")
        if current_job.has_target_data():
            formulation_data = current_job.target_profile_dataset
            
            # Type Filter Section
            # Extract all unique types from formulation profiles
            available_types = set()
            for profile_name, profile_df in formulation_data.items():
                if 'Type' in profile_df.columns:
                    profile_type = profile_df.iloc[0]['Type']
                    if pd.notna(profile_type) and str(profile_type).strip():
                        available_types.add(str(profile_type).strip())
                else:
                    available_types.add("Not specified")
            
            # Create filter options
            filter_options = ["All"] + sorted(list(available_types))
            selected_type_filter = st.selectbox(
                "Filter by Type:",
                filter_options,
                key="formulation_type_filter_summary"
            )
            
            # Filter profiles based on selected type
            if selected_type_filter == "All":
                filtered_formulation_data = formulation_data
            else:
                filtered_formulation_data = {}
                for profile_name, profile_df in formulation_data.items():
                    if 'Type' in profile_df.columns:
                        profile_type = str(profile_df.iloc[0]['Type']).strip()
                    else:
                        profile_type = "Not specified"
                    
                    if profile_type == selected_type_filter:
                        filtered_formulation_data[profile_name] = profile_df
            
            if filtered_formulation_data:
                # Formulation selection
                selected_formulation = st.selectbox(
                    "Select Formulation to View:",
                    list(filtered_formulation_data.keys()),
                    key="formulation_select_summary"
                )
                
                if selected_formulation:
                    selected_formulation_data = filtered_formulation_data[selected_formulation]
                    
                    # Show Type below the selector
                    if 'Type' in selected_formulation_data.columns:
                        formulation_type = selected_formulation_data.iloc[0]['Type']
                        st.markdown(f"**Type:** {formulation_type}")
                    
                    st.dataframe(selected_formulation_data, use_container_width=True)
                    
                    # Remove selected formulation button
                    if st.button(f"🗑️ Remove '{selected_formulation}'", key="remove_formulation_summary"):
                        if selected_formulation in current_job.target_profile_dataset:
                            del current_job.target_profile_dataset[selected_formulation]
                            # If no datasets left, set to None
                            if not current_job.target_profile_dataset:
                                current_job.target_profile_dataset = None
                            st.session_state.jobs[current_job_name] = current_job
                            st.success(f"Formulation '{selected_formulation}' removed from job")
                            st.rerun()
            else:
                if selected_type_filter != "All":
                    st.info(f"No formulation datasets of type '{selected_type_filter}' found in current job.")
                else:
                    st.info("No formulation datasets in current job.")
            
            # Clear all formulations button
            if st.button("🗑️ Clear All Formulation Data", key="clear_all_formulation_summary"):
                current_job.target_profile_dataset = None
                st.session_state.jobs[current_job_name] = current_job
                st.success("All formulation data cleared from job")
                st.rerun()
        else:
            st.info("No Formulation data saved in current job. Import or create Formulation data in 'Create target profile' tab.")

        st.divider()

        # Complete Target Profile Creation and Management
        st.markdown("### Complete Target Profiles")
        
        # Check if all three components are available
        has_api = current_job.has_api_data()
        has_polymer = hasattr(current_job, 'polymer_dataset') and current_job.polymer_dataset is not None
        has_formulations = current_job.has_target_data()
        
        if has_api and has_polymer and has_formulations:
            st.markdown("**Create Complete Target Profile**")
            st.info("✅ All components available (API + Polymer + Formulation)")
            
            # Profile creation section
            col_name, col_formulation, col_create = st.columns([2, 2, 1])
            
            with col_name:
                profile_name = st.text_input(
                    "Target Profile Name:",
                    placeholder="Enter unique profile name",
                    key="complete_profile_name"
                )
            
            with col_formulation:
                # Select formulation to combine with API and Polymer
                formulation_options = list(current_job.target_profile_dataset.keys())
                selected_formulation_for_profile = st.selectbox(
                    "Select Formulation:",
                    formulation_options,
                    key="formulation_for_complete_profile"
                )
            
            with col_create:
                st.write("")  # Space for alignment
                if st.button("🔗 Create Profile", key="create_complete_profile"):
                    if not profile_name.strip():
                        st.error("Please enter a profile name.")
                    elif not selected_formulation_for_profile:
                        st.error("Please select a formulation.")
                    else:
                        # Initialize complete_target_profiles if it doesn't exist
                        if not hasattr(current_job, 'complete_target_profiles'):
                            current_job.complete_target_profiles = {}
                        
                        # Check if profile name already exists
                        if profile_name.strip() in current_job.complete_target_profiles:
                            st.error(f"Profile name '{profile_name.strip()}' already exists. Please choose a different name.")
                        else:
                            # Create complete target profile
                            complete_profile = {
                                "api_data": current_job.api_dataset.copy(),
                                "polymer_data": current_job.polymer_dataset.copy(),
                                "formulation_data": current_job.target_profile_dataset[selected_formulation_for_profile].copy(),
                                "created_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            current_job.complete_target_profiles[profile_name.strip()] = complete_profile
                            st.session_state.jobs[current_job_name] = current_job
                            st.success(f"Complete target profile '{profile_name.strip()}' created successfully!")
                            st.rerun()
        else:
            st.markdown("**Create Complete Target Profile**")
            missing_components = []
            if not has_api:
                missing_components.append("API")
            if not has_polymer:
                missing_components.append("Hydrogel Polymer")
            if not has_formulations:
                missing_components.append("Formulation")
            
            st.warning(f"⚠️ Missing components: {', '.join(missing_components)}")
            st.info("Import all required components above to create complete target profiles.")
        
        # Display existing complete target profiles
        if hasattr(current_job, 'complete_target_profiles') and current_job.complete_target_profiles:
            st.markdown("**Existing Complete Target Profiles**")
            
            profiles = current_job.complete_target_profiles
            profile_names = list(profiles.keys())
            
            selected_complete_profile = st.selectbox(
                "Select Complete Target Profile to View:",
                profile_names,
                key="view_complete_profile_select"
            )
            
            if selected_complete_profile:
                profile_data = profiles[selected_complete_profile]
                
                # Show profile creation timestamp
                created_time = profile_data.get("created_timestamp", "Unknown")
                st.markdown(f"**Created:** {created_time}")
                
                # Show formulation type if available
                if ('formulation_data' in profile_data and 
                    'Type' in profile_data['formulation_data'].columns):
                    profile_type = profile_data['formulation_data'].iloc[0]['Type']
                    st.markdown(f"**Type:** {profile_type}")
                
                # Expandable sections for each component
                with st.expander("📋 API Component", expanded=False):
                    if profile_data.get('api_data') is not None:
                        st.dataframe(profile_data['api_data'], use_container_width=True)
                    else:
                        st.warning("No API data in this profile")
                
                with st.expander("🧪 Polymer Component", expanded=False):
                    if profile_data.get('polymer_data') is not None:
                        st.dataframe(profile_data['polymer_data'], use_container_width=True)
                    else:
                        st.warning("No Polymer data in this profile")
                
                with st.expander("⚗️ Formulation Component", expanded=False):
                    if profile_data.get('formulation_data') is not None:
                        st.dataframe(profile_data['formulation_data'], use_container_width=True)
                    else:
                        st.warning("No Formulation data in this profile")
                
                # Remove complete profile button
                col_remove, col_clear_all = st.columns(2)
                with col_remove:
                    if st.button(f"🗑️ Remove '{selected_complete_profile}'", key="remove_complete_profile"):
                        del current_job.complete_target_profiles[selected_complete_profile]
                        if not current_job.complete_target_profiles:
                            current_job.complete_target_profiles = {}
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Complete target profile '{selected_complete_profile}' removed")
                        st.rerun()
                
                with col_clear_all:
                    if st.button("🗑️ Clear All Profiles", key="clear_all_complete_profiles"):
                        current_job.complete_target_profiles = {}
                        st.session_state.jobs[current_job_name] = current_job
                        st.success("All complete target profiles cleared")
                        st.rerun()
        else:
            st.info("No complete target profiles created yet. Create profiles above to use in calculations.")
