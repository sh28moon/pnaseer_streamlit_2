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

    # Top-level tabs - now three tabs
    tab_api, tab_polymer, tab_target = st.tabs(["API Properties", "Polymer Properties", "Target Profile"])

    # ── Common function for database import tabs ────────────────────────────
    def render_database_tab(tab, db_type, db_key, tab_title):
        with tab:
            st.markdown(f'<p class="font-medium"><b>Import {tab_title} from Database</b></p>', unsafe_allow_html=True)

            # Ensure database stores exist
            if db_key not in st.session_state:
                st.session_state[db_key] = {}

            # Dataset selection section
            available_datasets = list(st.session_state[db_key].keys())
            
            if available_datasets:
                selected_dataset = st.selectbox(
                    "Select Dataset:",
                    available_datasets,
                    key=f"{db_key}_dataset_select"
                )
            else:
                st.warning(f"⚠️ No datasets available in {db_type} database. Please import datasets in Database Management first.")
                selected_dataset = None

            # Row selection section
            selected_row = None
            selected_data = None
            
            if selected_dataset and available_datasets:
                dataset_df = st.session_state[db_key][selected_dataset]
                
                # Display dataset preview
                with st.expander(f"📄 Dataset Preview: {selected_dataset}", expanded=False):
                    st.dataframe(dataset_df, use_container_width=True)
                    st.write(f"Shape: {dataset_df.shape[0]} rows × {dataset_df.shape[1]} columns")
                
                # Row selection
                st.markdown("**Select Row from Dataset:**")
                
                if len(dataset_df) > 1:
                    # Multiple rows - create options for selection
                    if 'Name' in dataset_df.columns:
                        # Use Name column values if available
                        row_options = []
                        for idx, row in dataset_df.iterrows():
                            name = row['Name'] if pd.notna(row['Name']) else f"Row {idx + 1}"
                            row_options.append(f"{name} (Row {idx + 1})")
                        
                        selected_row_option = st.selectbox(
                            "Choose row:",
                            row_options,
                            key=f"{db_key}_row_select"
                        )
                        
                        # Extract row index from selection
                        selected_row_index = int(selected_row_option.split("(Row ")[1].split(")")[0]) - 1
                        selected_data = dataset_df.iloc[[selected_row_index]].copy()
                        selected_row = selected_row_index
                    else:
                        # Use row numbers if no Name column
                        row_numbers = [f"Row {i+1}" for i in range(len(dataset_df))]
                        selected_row_display = st.selectbox(
                            "Choose row:",
                            row_numbers,
                            key=f"{db_key}_row_select"
                        )
                        selected_row_index = row_numbers.index(selected_row_display)
                        selected_data = dataset_df.iloc[[selected_row_index]].copy()
                        selected_row = selected_row_index
                else:
                    # Single row
                    st.info("Dataset contains only one row - automatically selected")
                    selected_data = dataset_df.copy()
                    selected_row_index = 0
                    selected_row = 0

            st.divider() 

            # Data summary and save section
            st.markdown("**Data Summary**")
            
            # Show current selection
            if selected_data is not None:
                st.markdown(f"**Selected:** {db_type} → {selected_dataset} → Row {selected_row + 1}")
                st.dataframe(selected_data, use_container_width=True)
            else:
                st.info(f"No {tab_title.lower()} selected from database yet.")
            
            # Show current job data if exists (check for API data for both tabs)
            if current_job.has_api_data():
                with st.expander(f"📋 Current Job {tab_title}", expanded=False):
                    st.dataframe(current_job.api_dataset, use_container_width=True)
                    st.success(f"✅ {tab_title} saved to current job")
            
            # Save and Clear buttons
            col1, col2 = st.columns(2)
            with col1:
                # Save button - enabled if data is selected
                button_text = f"Update {tab_title}" if current_job.has_api_data() else f"Save {tab_title}"
                save_disabled = selected_data is None
                
                if st.button(button_text, key=f"save_{db_key}_data", disabled=save_disabled):
                    if selected_data is not None:
                        current_job.api_dataset = selected_data
                        st.session_state.jobs[current_job_name] = current_job
                        action = "updated" if current_job.has_api_data() else "saved"
                        st.success(f"{tab_title} {action} in job '{current_job_name}' from {db_type} → {selected_dataset}")
                        st.rerun()
                    else:
                        st.error(f"No {tab_title.lower()} selected. Please select data from database first.")
            
            with col2:
                # Clear data from job
                if current_job.has_api_data():
                    if st.button(f"🗑️ Clear {tab_title}", key=f"clear_{db_key}_data", help=f"Remove {tab_title.lower()} from current job"):
                        current_job.api_dataset = None
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"{tab_title} cleared from job '{current_job_name}'")
                        st.rerun()

    # ── API Properties Tab ──────────────────────────────────────────────────
    render_database_tab(tab_api, "API", "common_api_datasets", "API Dataset")

    # ── Polymer Properties Tab ──────────────────────────────────────────────
    render_database_tab(tab_polymer, "Polymers", "polymer_datasets", "Polymer Dataset")

    # ── Target Profile Tab ───────────────────────────────────────────────────
    with tab_target:
        # st.markdown('<p class="font-medium"><b>Target Profile</b></p>', unsafe_allow_html=True)

        # Ensure data stores exist
        if "input_target_datasets" not in st.session_state:
            st.session_state["input_target_datasets"] = {}
            st.session_state["input_target_manual_count"] = 0

        # Row 1: Target Profile Input - 2 columns with same height
        # st.markdown("**Target Profile Input**")
        col_import, col_manual = st.columns(2)

        # Left Column: Import Data
        with col_import:
            st.markdown('<p class="font-medium"><b>Import Target Profile Data</b></p>', unsafe_allow_html=True)          

            uploaded_tp = st.file_uploader(
                "Import Data (CSV file with Name, Modulus, Encapsulation Rate, Release Time, Type columns)",
                type=["csv"],
                key="target_profile_file"
            )
            if uploaded_tp:
                try:
                    df_tp = pd.read_csv(uploaded_tp)
                    
                    # Validate data structure
                    if 'Name' not in df_tp.columns:
                        st.error("❌ Target CSV must have a 'Name' column for dataset identification.")
                    elif 'Type' not in df_tp.columns:
                        st.error("❌ Target CSV must have a 'Type' column for categorization.")
                    elif len(df_tp.columns) < 5:
                        st.error(f"❌ Invalid file structure. Expected at least 5 columns (Name, Modulus, Encapsulation Rate, Release Time, Type), got {len(df_tp.columns)}.")
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
                            st.success(f"✅ {len(target_datasets)} target datasets loaded")
                        else:
                            st.error("❌ No valid datasets found. Check that Name column contains values.")
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
                    
            # Save imported data to job button
            if st.session_state.get("temp_target_data"):
                if st.button("Save Data", key="save_imported_to_job"):
                    temp_data = st.session_state["temp_target_data"]
                    if current_job.has_target_data():
                        current_job.target_profile_dataset.update(temp_data)
                    else:
                        current_job.target_profile_dataset = temp_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"{len(temp_data)} imported dataset(s) saved to job")
                    st.rerun()

        # Right Column: Manual Input
        with col_manual:
            st.markdown("**Manual Input**")
            
            # Dataset name input
            dataset_name = st.text_input("Dataset Name", placeholder="Enter dataset name", key="manual_dataset_name")
            
            # Type input
            dataset_type = st.text_input("Type", placeholder="Enter dataset type (e.g., Standard, High-Performance)", key="manual_dataset_type")
            
            # Parameter inputs
            modulus = st.number_input("Modulus[MPa]", min_value=0.0, format="%.2f", key="tp_modulus")
            encapsulation_rate = st.number_input("Encapsulation Rate(0 ~ 1)", min_value=0.0, format="%.2f", key="tp_encapsulation_rate")
            release_time = st.number_input("Release Time[Week]", min_value=0.0, format="%.2f", key="tp_release_time")

            # Single button to add and save directly to job
            if st.button("Save Data", key="add_manual_to_job"):
                if not dataset_name.strip():
                    st.error("Please enter a dataset name.")
                elif not dataset_type.strip():
                    st.error("Please enter a dataset type.")
                else:
                    # Create manual input dataset with 5 columns including name and type
                    df_manual = pd.DataFrame([{
                        "Name": dataset_name.strip(),
                        "Modulus": modulus,
                        "Encapsulation Rate": encapsulation_rate,
                        "Release Time (Day)": release_time,
                        "Type": dataset_type.strip()
                    }])
                    
                    # Save directly to job using the dataset name as key
                    if current_job.has_target_data():
                        current_job.target_profile_dataset[dataset_name.strip()] = df_manual
                    else:
                        current_job.target_profile_dataset = {dataset_name.strip(): df_manual}
                    
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Dataset '{dataset_name.strip()}' added to job")
                    st.rerun()

            # Global clear button
            # if current_job.has_target_data():
            #     if st.button("🗑️ Clear All Target Data", key="clear_all_target_data"):
            #         current_job.target_profile_dataset = None
            #         st.session_state.jobs[current_job_name] = current_job
            #         st.success(f"All target data cleared from job")
            #         st.rerun()

        st.divider()

        # Row 2: Input Summary - 2 columns with same height  
        st.markdown("**Input Summary**")
        
        # Type Filter Section
        if current_job.has_target_data():
            job_data = current_job.target_profile_dataset
            
            # Extract all unique types from target profiles
            available_types = set()
            for profile_name, profile_df in job_data.items():
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
                key="target_type_filter"
            )
            
            # Filter profiles based on selected type
            if selected_type_filter == "All":
                filtered_job_data = job_data
            else:
                filtered_job_data = {}
                for profile_name, profile_df in job_data.items():
                    if 'Type' in profile_df.columns:
                        profile_type = str(profile_df.iloc[0]['Type']).strip()
                    else:
                        profile_type = "Not specified"
                    
                    if profile_type == selected_type_filter:
                        filtered_job_data[profile_name] = profile_df
        else:
            filtered_job_data = {}
            selected_type_filter = "All"
        
        col_functions, col_diagram = st.columns(2)

        # Left Column: Functions (data selection, table, remove button)
        with col_functions:
            # Only show data from current job (filtered by type)
            if filtered_job_data:
                selected = st.selectbox(
                    "Select Dataset from Job",
                    list(filtered_job_data.keys()),
                    key="job_target_select"
                )
                
                # Remove dataset button
                if st.button(f"Remove '{selected}' profile", key="remove_selected_dataset"):
                    # Remove the selected dataset from job (from original data, not filtered)
                    if selected in current_job.target_profile_dataset:
                        del current_job.target_profile_dataset[selected]
                        # If no datasets left, set to None
                        if not current_job.target_profile_dataset:
                            current_job.target_profile_dataset = None
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Dataset '{selected}' removed from job")
                        st.rerun()
                
                df_sel = filtered_job_data[selected]
                
                # Show table
                st.markdown("**Data Table**")
                st.dataframe(df_sel, use_container_width=True)
                
                # Show Type below the table
                if 'Type' in df_sel.columns:
                    dataset_type = df_sel.iloc[0]['Type']
                    st.markdown(f"**Type:** {dataset_type}")
                else:
                    st.markdown("**Type:** Not specified")
            else:
                if current_job.has_target_data():
                    if selected_type_filter != "All":
                        st.info(f"No target datasets of type '{selected_type_filter}' found in current job.")
                    else:
                        st.info("No target datasets in current job. Import data or add manual input to get started.")
                else:
                    st.info("No target datasets in current job. Import data or add manual input to get started.")
                selected = None
                df_sel = None

        # Right Column: Comparative Radar Diagram
        with col_diagram:
            if filtered_job_data:
                # Collect all target profiles for comparison (filtered by type)
                all_profiles = []
                profile_names = []
                
                for profile_name, profile_df in filtered_job_data.items():
                    if len(profile_df.columns) >= 5:  # Check if we have enough columns (Name + 3 data + Type)
                        # Extract values from columns 1, 2, 3 (skip Name column, before Type column)
                        data_columns = profile_df.columns[1:4]
                        vals = profile_df.iloc[0][data_columns].tolist()
                        # Convert to numeric values, handling any string formatting
                        numeric_vals = []
                        for val in vals:
                            if isinstance(val, str):
                                # Remove any units or percentage signs and convert to float
                                clean_val = val.replace('%', '').replace('Day', '').replace('MPa', '').strip()
                                numeric_vals.append(float(clean_val))
                            else:
                                numeric_vals.append(float(val))
                        all_profiles.append(numeric_vals)
                        profile_names.append(profile_name)
                
                if all_profiles:
                    # Normalize values for better shape comparison
                    all_profiles_array = np.array(all_profiles)
                    
                    # Get min and max for each parameter across all profiles
                    param_mins = np.min(all_profiles_array, axis=0)
                    param_maxs = np.max(all_profiles_array, axis=0)
                    
                    # Normalize to 0-100 scale with minimum shape constraint
                    normalized_profiles = []
                    for profile in all_profiles:
                        normalized = []
                        for i, val in enumerate(profile):
                            param_range = param_maxs[i] - param_mins[i]
                            if param_range > 0:
                                # Normalize to 20-100 range to avoid too acute shapes
                                norm_val = 20 + ((val - param_mins[i]) / param_range) * 80
                            else:
                                # If all values are the same, set to middle value
                                norm_val = 60
                            normalized.append(norm_val)
                        normalized_profiles.append(normalized)
                    
                    # Create radar chart
                    labels = ["Modulus", "Encapsulation\nRate", "Release Time\n(Week)"]
                    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                    
                    # Create figure with better sizing
                    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
                    
                    # Color palette for different profiles
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                    
                    # Plot each profile
                    for i, (norm_profile, name) in enumerate(zip(normalized_profiles, profile_names)):
                        # Close the radar chart
                        values = norm_profile + norm_profile[:1]
                        angles_plot = angles + angles[:1]
                        
                        color = colors[i % len(colors)]
                        
                        # Plot line and fill
                        ax.plot(angles_plot, values, marker="o", linewidth=2.5, 
                               markersize=6, label=name, color=color, alpha=0.8)
                        ax.fill(angles_plot, values, alpha=0.15, color=color)
                        
                        # Highlight selected profile
                        if selected and name == selected:
                            ax.plot(angles_plot, values, marker="s", linewidth=4, 
                                   markersize=8, color=color, alpha=1.0)
                    
                    # Customize radar chart
                    ax.set_thetagrids(np.degrees(angles), labels)
                    ax.set_ylim(0, 100)
                    
                    # Set radial ticks and labels
                    ax.set_yticks([20, 40, 60, 80, 100])
                    ax.set_yticklabels(['Min', '25%', '50%', '75%', 'Max'], 
                                     fontsize=8, alpha=0.7)
                    
                    # Position title higher to avoid overlap, include filter info
                    if selected_type_filter == "All":
                        title = "Target Profiles Comparison"
                    else:
                        title = f"Target Profiles Comparison\n(Type: {selected_type_filter})"
                    ax.set_title(title, y=1.15, fontsize=14, fontweight='bold', pad=20)
                    
                    # Add legend outside the plot area
                    ax.legend(loc='upper left', bbox_to_anchor=(-0.1, 1.0), 
                             frameon=True, fancybox=True, shadow=True)
                    
                    # Customize grid
                    ax.grid(True, alpha=0.3)
                    ax.set_facecolor('#fafafa')
                    
                    # Add actual values as text annotations for selected profile
                    if selected and selected in profile_names:
                        selected_idx = profile_names.index(selected)
                        actual_values = all_profiles[selected_idx]
                        
                        st.pyplot(fig)
                        
                        # Show actual values and type below chart
                        selected_profile_df = filtered_job_data[selected]
                        profile_type = selected_profile_df.iloc[0]['Type'] if 'Type' in selected_profile_df.columns else "Not specified"
                        
                        st.markdown(f"**Selected Profile: '{selected}' (Type: {profile_type})**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Modulus", f"{actual_values[0]:.2f}", delta=None)
                        with col2:
                            st.metric("Encap Rate", f"{actual_values[1]:.2f}", delta=None)
                        with col3:
                            st.metric("Release Time", f"{actual_values[2]:.2f}", delta=None)
                    else:
                        st.pyplot(fig)
                        
                        # Show summary statistics
                        st.markdown("**Dataset Summary:**")
                        st.write(f"• **Total Profiles:** {len(profile_names)}")
                        if selected_type_filter != "All":
                            st.write(f"• **Filtered by Type:** {selected_type_filter}")
                        if len(profile_names) > 1 and selected:
                            st.write(f"• **Selected:** {selected}")
                            st.write("• **Comparison:** Normalized 20-100 scale")
                else:
                    if selected_type_filter != "All":
                        st.warning(f"No valid target profiles found for type '{selected_type_filter}' with sufficient data columns (Name, Modulus, Encapsulation Rate, Release Time, Type required)")
                    else:
                        st.warning("No valid target profiles found with sufficient data columns (Name, Modulus, Encapsulation Rate, Release Time, Type required)")
            else:
                if current_job.has_target_data() and selected_type_filter != "All":
                    st.info(f"No target datasets of type '{selected_type_filter}' found. Try selecting 'All' or a different type.")
                else:
                    st.info("No target datasets in current job. Add target profiles to view comparison diagram.")
