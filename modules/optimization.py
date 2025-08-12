# modules/optimization.py
import streamlit as st
import pandas as pd
import time
import random
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.header("Calculation")

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    st.info(f"📁 Working on job: **{current_job_name}**")

    # Top-level tabs
    tab_atps = st.tabs(["ATPS Partition"])[0]

    def render_model_tab(prefix, tab):
        with tab:
            # All selections in one row with three columns
            st.markdown('<p class="font-medium"><b>Input Data Selection & Model Selection</b></p>', unsafe_allow_html=True)
            
            # Three-column layout: Input Data Selection (1 col) + Target Selection (1 col) + Model Selection (1 col)
            col1, col2, col3 = st.columns(3)
            
            # Column 1: API and Polymer Data Selection (Input Data Selection - Part 1)
            with col1:
                st.markdown("**API/Polymer Data**")
                
                # Initialize selection variables for both API and Polymer
                selected_api_data = None
                selected_api_index = None
                selected_api_name = None
                selected_polymer_data = None
                selected_polymer_index = None
                selected_polymer_name = None
                
                # Upper togglebox: API Data
                st.markdown("*API Data:*")
                if "common_api_datasets" in st.session_state and st.session_state["common_api_datasets"]:
                    api_datasets = st.session_state["common_api_datasets"]
                    api_dataset_options = [""] + list(api_datasets.keys())
                    
                    selected_api_dataset = st.selectbox(
                        "",
                        api_dataset_options,
                        key=f"{prefix}_api_dataset_select"
                    )
                    
                    if selected_api_dataset:
                        api_data = api_datasets[selected_api_dataset]
                        
                        # API row selection
                        if len(api_data) > 1:
                            if 'Name' in api_data.columns:
                                api_name_options = api_data['Name'].tolist()
                                selected_api_name = st.selectbox(
                                    "",
                                    api_name_options,
                                    key=f"{prefix}_api_row_select"
                                )
                                selected_api_index = api_name_options.index(selected_api_name)
                                selected_api_data = api_data.iloc[[selected_api_index]]
                            else:
                                first_column_values = api_data.iloc[:, 0].tolist()
                                first_column_display = [str(val) if pd.notna(val) else f"Row {i+1}" for i, val in enumerate(first_column_values)]
                                
                                selected_api_row = st.selectbox(
                                    "",
                                    first_column_display,
                                    key=f"{prefix}_api_row_select"
                                )
                                selected_api_index = first_column_display.index(selected_api_row)
                                selected_api_data = api_data.iloc[[selected_api_index]]
                                selected_api_name = selected_api_row
                        else:
                            # Single row
                            selected_api_data = api_data
                            selected_api_index = 0
                            if 'Name' in api_data.columns:
                                selected_api_name = api_data['Name'].iloc[0] if pd.notna(api_data['Name'].iloc[0]) else str(api_data.iloc[0, 0])
                            else:
                                selected_api_name = str(api_data.iloc[0, 0]) if pd.notna(api_data.iloc[0, 0]) else "Row 1"
                else:
                    st.selectbox("", ["No API datasets available"], disabled=True, key=f"{prefix}_api_placeholder")
                
                # Lower togglebox: Polymer Data
                st.markdown("*Polymer Data:*")
                if "polymer_datasets" in st.session_state and st.session_state["polymer_datasets"]:
                    polymer_datasets = st.session_state["polymer_datasets"]
                    polymer_dataset_options = [""] + list(polymer_datasets.keys())
                    
                    selected_polymer_dataset = st.selectbox(
                        "",
                        polymer_dataset_options,
                        key=f"{prefix}_polymer_dataset_select"
                    )
                    
                    if selected_polymer_dataset:
                        polymer_data = polymer_datasets[selected_polymer_dataset]
                        
                        # Polymer row selection
                        if len(polymer_data) > 1:
                            if 'Name' in polymer_data.columns:
                                polymer_name_options = polymer_data['Name'].tolist()
                                selected_polymer_name = st.selectbox(
                                    "",
                                    polymer_name_options,
                                    key=f"{prefix}_polymer_row_select"
                                )
                                selected_polymer_index = polymer_name_options.index(selected_polymer_name)
                                selected_polymer_data = polymer_data.iloc[[selected_polymer_index]]
                            else:
                                first_column_values = polymer_data.iloc[:, 0].tolist()
                                first_column_display = [str(val) if pd.notna(val) else f"Row {i+1}" for i, val in enumerate(first_column_values)]
                                
                                selected_polymer_row = st.selectbox(
                                    "",
                                    first_column_display,
                                    key=f"{prefix}_polymer_row_select"
                                )
                                selected_polymer_index = first_column_display.index(selected_polymer_row)
                                selected_polymer_data = polymer_data.iloc[[selected_polymer_index]]
                                selected_polymer_name = selected_polymer_row
                        else:
                            # Single row
                            selected_polymer_data = polymer_data
                            selected_polymer_index = 0
                            if 'Name' in polymer_data.columns:
                                selected_polymer_name = polymer_data['Name'].iloc[0] if pd.notna(polymer_data['Name'].iloc[0]) else str(polymer_data.iloc[0, 0])
                            else:
                                selected_polymer_name = str(polymer_data.iloc[0, 0]) if pd.notna(polymer_data.iloc[0, 0]) else "Row 1"
                else:
                    st.selectbox("", ["No Polymer datasets available"], disabled=True, key=f"{prefix}_polymer_placeholder")
            
            # Column 2: Target Profile Data (Input Data Selection - Part 2)
            with col2:
                st.markdown("**Target Profile Data**")
                
                # Initialize target selection variables
                selected_target_data = None
                selected_target_name = None
                
                if current_job.has_target_data():
                    target_data = current_job.target_profile_dataset
                    
                    # Add Type filter for target selection
                    # Extract all unique types from target profiles
                    available_types = set()
                    for profile_name, profile_df in target_data.items():
                        if 'Type' in profile_df.columns:
                            profile_type = profile_df.iloc[0]['Type']
                            if pd.notna(profile_type) and str(profile_type).strip():
                                available_types.add(str(profile_type).strip())
                        else:
                            available_types.add("Not specified")
                    
                    # Type filter for calculation
                    if available_types:
                        filter_options = ["All"] + sorted(list(available_types))
                        selected_type_filter = st.selectbox(
                            "Filter by Type:",
                            filter_options,
                            key=f"{prefix}_target_type_filter"
                        )
                        
                        # Filter targets based on type
                        if selected_type_filter == "All":
                            filtered_targets = target_data
                        else:
                            filtered_targets = {}
                            for profile_name, profile_df in target_data.items():
                                if 'Type' in profile_df.columns:
                                    profile_type = str(profile_df.iloc[0]['Type']).strip()
                                else:
                                    profile_type = "Not specified"
                                
                                if profile_type == selected_type_filter:
                                    filtered_targets[profile_name] = profile_df
                    else:
                        filtered_targets = target_data
                        selected_type_filter = "All"
                    
                    # Target Profile Data Selection
                    if filtered_targets:
                        target_names = list(filtered_targets.keys())
                        selected_target_name = st.selectbox(
                            "Select Target Dataset",
                            target_names,
                            key=f"{prefix}_target_select"
                        )
                        
                        if selected_target_name:
                            selected_target_data = filtered_targets[selected_target_name]
                    else:
                        st.warning(f"❌ No targets of type '{selected_type_filter}' found")
                        selected_target_name = None
                else:
                    st.error("❌ No target data in current job")
                    st.info("💡 Add target profiles in Input Target → Target Profile")
                    selected_target_name = None
            
            # Column 3: Model Selection
            with col3:
                st.markdown("**Model Selection**")
                
                # Compact model import
                if not current_job.has_model_data():
                    uploaded = st.file_uploader(
                        "Import Model (CSV)",
                        type=["csv"],
                        key=f"{prefix}_import",
                        label_visibility="collapsed"
                    )
                    if uploaded:
                        try:
                            df = pd.read_csv(uploaded)
                            
                            if 'Name' not in df.columns or len(df) == 0:
                                st.error("❌ Invalid model file")
                            else:
                                # Create separate model datasets for each row
                                model_datasets = {}
                                for index, row in df.iterrows():
                                    model_name = str(row['Name']).strip()
                                    if model_name:
                                        model_df = pd.DataFrame([row])
                                        model_datasets[model_name] = model_df
                                
                                if model_datasets:
                                    current_job.model_dataset = model_datasets
                                    st.session_state.jobs[current_job_name] = current_job
                                    st.rerun()
                                
                        except Exception as e:
                            st.error("❌ Error reading file")

                # Model selection at same level as other selectboxes
                if current_job.has_model_data():
                    model_data = current_job.model_dataset
                    model_names = list(model_data.keys())           
                    
                    selected = st.selectbox(
                        "Select Model",
                        model_names,
                        key=f"{prefix}_select"
                    )
                    
                    # Compact clear button
                    if st.button(f"🗑️ Clear", key=f"clear_model_{prefix}"):
                        current_job.model_dataset = None
                        st.session_state.jobs[current_job_name] = current_job
                        st.rerun()
                else:
                    selected = None
                    # Placeholder to maintain height
                    st.selectbox(
                        "Select Model",
                        ["No models available"],
                        disabled=True,
                        key=f"{prefix}_select_placeholder"
                    )

            st.divider()

            # Calculate section
            st.subheader("Input Review and Submit Job")
            
            # Show four separate tables with full values
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Selected API Data**")
                if selected_api_data is not None and selected_api_name is not None:
                    st.markdown(f"*{selected_api_name}*")
                    st.dataframe(selected_api_data, use_container_width=True)
                else:
                    st.info("No API data selected")
            
            with col2:
                st.markdown("**Selected Polymer Data**")
                if selected_polymer_data is not None and selected_polymer_name is not None:
                    st.dataframe(selected_polymer_data, use_container_width=True)
                else:
                    st.info("No Polymer data selected")
            
            with col3:
                st.markdown("**Selected Target Profile**")
                if selected_target_data is not None:
                    # Show type information if available
                    if 'Type' in selected_target_data.columns:
                        target_type = selected_target_data.iloc[0]['Type']
                        st.markdown(f"*{selected_target_name}* (Type: {target_type})")
                    else:
                        st.markdown(f"*{selected_target_name}*")
                    st.dataframe(selected_target_data, use_container_width=True)
                else:
                    st.info("No target data selected")
            
            with col4:
                st.markdown("**Selected Model**")
                if selected and current_job.get_model_status():
                    st.markdown(f"*{selected}*")
                    model_df = current_job.model_dataset[selected]
                    st.dataframe(model_df, use_container_width=True)
                else:
                    st.info("No model selected")
            
            # Submit button and Clear Results button
            has_api_data = selected_api_data is not None and selected_api_name is not None
            has_polymer_data = selected_polymer_data is not None and selected_polymer_name is not None
            has_target_data = current_job.has_target_data() and selected_target_data is not None
            has_model_data = current_job.get_model_status() and selected
            can_submit = has_api_data and has_polymer_data and has_target_data and has_model_data
            
            col_submit, col_clear = st.columns(2)
            
            with col_submit:
                if st.button("Submit Job", key=f"{prefix}_run", disabled=not can_submit):
                    if not can_submit:
                        st.error("Please ensure API data, Polymer data, target data, and model are all selected before submitting.")
                    else:
                        progress = st.progress(0)
                        for i in range(101):
                            time.sleep(0.02)
                            progress.progress(i)
                        st.success("Completed Calculation")

                        # Create comprehensive result datasets during optimization
                        import datetime
                        
                        # Generate composition results - 3 rows with 3 components, all percentages sum to 100%
                        composition_results = []
                        for i in range(3):  # Create 3 rows
                            buffer_pct = random.randint(80, 95)  # Buffer between 80-95%
                            remaining_pct = 100 - buffer_pct
                            
                            # Distribute remaining percentage between Gel Polymer and Co-polymer
                            gel_polymer_pct = random.randint(1, remaining_pct - 1)
                            co_polymer_pct = remaining_pct - gel_polymer_pct
                            
                            composition_results.append({
                                "Row": f"Formulation {i+1}",
                                "Gel Polymer w/w": f"{gel_polymer_pct}%",
                                "Co-polymer w/w": f"{co_polymer_pct}%", 
                                "Buffer w/w": f"{buffer_pct}%"
                            })
                        
                        # Generate performance metrics
                        performance_metrics = {
                            "metrics": ["Stability", "Efficacy", "Safety", "Bioavailability", "Manufacturability"],
                            "values": [random.uniform(0.6, 1.0) for _ in range(5)],
                            "ratings": []
                        }
                        # Add ratings based on values
                        performance_metrics["ratings"] = [
                            "Excellent" if v > 0.8 else "Good" if v > 0.6 else "Fair" 
                            for v in performance_metrics["values"]
                        ]
                        
                        # Generate performance trend data for all 3 formulations
                        # Get Release Time from target data (handle Type column)
                        if len(selected_target_data.columns) >= 4:
                            # Find release time column (should be 3rd data column, considering Type might be last)
                            if 'Type' in selected_target_data.columns:
                                # Type column exists, find release time in data columns
                                data_columns = [col for col in selected_target_data.columns if col not in ['Name', 'Type']]
                                if len(data_columns) >= 3:
                                    release_time_value = selected_target_data.iloc[0][data_columns[2]]  # Third data column
                                else:
                                    release_time_value = 10  # fallback
                            else:
                                # No Type column, use 4th column (index 3)
                                release_time_value = selected_target_data.iloc[0, 3]
                            
                            # Convert to numeric if it's a string with units
                            if isinstance(release_time_value, str):
                                release_time_value = float(release_time_value.replace('%', '').replace('Day', '').replace('Week', '').strip())
                            elif not isinstance(release_time_value, (int, float)):
                                release_time_value = float(release_time_value)
                        else:
                            release_time_value = 10  # Default fallback
                        
                        # Generate fixed performance trend data for all 3 formulations
                        performance_trends = {}
                        x_points = 10
                        x_values = np.linspace(0, release_time_value, x_points).tolist()
                        
                        # Set seed for reproducible results within this job
                        np.random.seed(hash(current_job_name + selected_api_name + selected_target_name) % 2147483647)
                        
                        start_values = [0.1, 0.15, 0.08]
                        end_values = [0.85, 0.92, 0.88]
                        
                        for i in range(3):
                            formulation_name = f"Formulation {i+1}"
                            base_trend = np.linspace(start_values[i], end_values[i], x_points)
                            noise = np.random.normal(0, 0.02, x_points)
                            y_values = base_trend + noise
                            
                            # Ensure values stay within 0-1 range and maintain upward trend
                            y_values = np.clip(y_values, 0, 1)
                            y_values = np.sort(y_values)  # Force upward trend
                            
                            performance_trends[formulation_name] = {
                                "x_values": x_values,
                                "y_values": y_values.tolist(),
                                "release_time": release_time_value
                            }
                        
                        # Generate evaluation diagrams data for each formulation
                        # Set seed for consistent evaluation results per job
                        np.random.seed(hash(current_job_name + selected_api_name + selected_target_name + "evaluation") % 2147483647)
                        
                        evaluation_diagrams_data = {}
                        
                        # Generate evaluation data for each of the 3 formulations
                        for i in range(3):
                            formulation_name = f"Formulation {i+1}"
                            
                            # Safety & Stability Score (0-10) - different for each formulation
                            safety_stability_scores = {
                                "Degradability": random.randint(1, 10),
                                "Cytotoxicity": random.randint(1, 10),
                                "Immunogenicity": random.randint(1, 10)
                            }
                            
                            # Formulation Score (0-10) - different for each formulation
                            formulation_scores = {
                                "Durability": random.randint(1, 10),
                                "Injectability": random.randint(1, 10),
                                "Strength": random.randint(1, 10)
                            }
                            
                            evaluation_diagrams_data[formulation_name] = {
                                "safety_stability": safety_stability_scores,
                                "formulation": formulation_scores,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        
                        # Create comprehensive result data with all generated datasets
                        result_data = {
                            "type": prefix,
                            "model_name": selected,
                            "selected_api_data": selected_api_data,
                            "selected_api_name": selected_api_name,
                            "selected_api_row": selected_api_index if selected_api_index is not None else 0,
                            "selected_polymer_data": selected_polymer_data,
                            "selected_polymer_name": selected_polymer_name,
                            "selected_polymer_row": selected_polymer_index if selected_polymer_index is not None else 0,
                            "selected_target_data": selected_target_data,
                            "selected_target_name": selected_target_name,
                            "selected_target_type": selected_target_data.iloc[0]['Type'] if 'Type' in selected_target_data.columns else "Not specified",
                            "target_type_filter": selected_type_filter if 'selected_type_filter' in locals() else "All",
                            "model_data": current_job.model_dataset[selected] if selected else None,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "completed",
                            
                            # Generated result datasets
                            "composition_results": composition_results,
                            "performance_metrics": performance_metrics,
                            "performance_trends": performance_trends,  # Fixed performance trend data
                            "evaluation_diagrams": evaluation_diagrams_data  # Evaluation diagrams data
                        }
                        
                        current_job.result_dataset = result_data
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Results with datasets generated and saved to job '{current_job_name}'")
            
            with col_clear:
                # Clear Results button - only enabled if results exist
                has_results = current_job.has_result_data()
                
                if st.button("🗑️ Clear Results", key=f"{prefix}_clear_results", 
                           disabled=not has_results, 
                           help="Remove all calculation results from current job"):
                    if has_results:
                        # Clear optimization results
                        current_job.result_dataset = None
                        
                        # Also clear evaluation diagrams display state
                        if 'show_evaluation_diagrams' in st.session_state:
                            st.session_state.show_evaluation_diagrams = False
                        
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"All results cleared from job '{current_job_name}'")
                        st.rerun()
                
                # Show results status
                if has_results:
                    st.info("✅ Results available")
                else:
                    st.info("ℹ️ No results to clear")

    # Render each tab
    render_model_tab("atps", tab_atps)
