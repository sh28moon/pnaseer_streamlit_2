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

    # Top-level tabs
    tab_atps = st.tabs(["ATPS Partition"])[0]

    def render_model_tab(prefix, tab):
        with tab:
            # Two-column layout: Target Profile Selection (2 cols) + Model Selection (1 col)
            st.markdown('<p class="font-medium"><b>Target Profile Selection & Model Selection</b></p>', unsafe_allow_html=True)
            
            col_target, col_model = st.columns([2, 1])
            
            # Column 1: Target Profile Selection (replaces separate API/Polymer/Target selection)
            with col_target:
                st.markdown("**Target Profile Selection**")
                
                # Initialize target profile selection variables
                selected_target_profile = None
                selected_target_profile_name = None
                
                # Check if job has complete target profiles
                if hasattr(current_job, 'complete_target_profiles') and current_job.complete_target_profiles:
                    target_profiles = current_job.complete_target_profiles
                    
                    # Type filter for target profiles
                    available_types = set()
                    for profile_name, profile_data in target_profiles.items():
                        if 'formulation_data' in profile_data and 'Type' in profile_data['formulation_data'].columns:
                            profile_type = profile_data['formulation_data'].iloc[0]['Type']
                            if pd.notna(profile_type) and str(profile_type).strip():
                                available_types.add(str(profile_type).strip())
                        else:
                            available_types.add("Not specified")
                    
                    # Type filter
                    if available_types:
                        filter_options = ["All"] + sorted(list(available_types))
                        selected_type_filter = st.selectbox(
                            "Filter by Type:",
                            filter_options,
                            key=f"{prefix}_target_profile_type_filter"
                        )
                        
                        # Filter target profiles based on type
                        if selected_type_filter == "All":
                            filtered_profiles = target_profiles
                        else:
                            filtered_profiles = {}
                            for profile_name, profile_data in target_profiles.items():
                                if 'formulation_data' in profile_data and 'Type' in profile_data['formulation_data'].columns:
                                    profile_type = str(profile_data['formulation_data'].iloc[0]['Type']).strip()
                                else:
                                    profile_type = "Not specified"
                                
                                if profile_type == selected_type_filter:
                                    filtered_profiles[profile_name] = profile_data
                    else:
                        filtered_profiles = target_profiles
                        selected_type_filter = "All"
                    
                    # Target Profile Selection
                    if filtered_profiles:
                        profile_names = list(filtered_profiles.keys())
                        selected_target_profile_name = st.selectbox(
                            "Select Target Profile:",
                            profile_names,
                            key=f"{prefix}_target_profile_select"
                        )
                        
                        if selected_target_profile_name:
                            selected_target_profile = filtered_profiles[selected_target_profile_name]
                            
                            # Show profile components summary
                            with st.expander(f"📄 Target Profile Details: {selected_target_profile_name}", expanded=False):
                                # API Data
                                if 'api_data' in selected_target_profile and selected_target_profile['api_data'] is not None:
                                    st.markdown("**API Data:**")
                                    st.dataframe(selected_target_profile['api_data'], use_container_width=True)
                                else:
                                    st.warning("⚠️ No API data in this profile")
                                
                                # Polymer Data
                                if 'polymer_data' in selected_target_profile and selected_target_profile['polymer_data'] is not None:
                                    st.markdown("**Hydrogel Polymer Data:**")
                                    st.dataframe(selected_target_profile['polymer_data'], use_container_width=True)
                                else:
                                    st.warning("⚠️ No Polymer data in this profile")
                                
                                # Formulation Data
                                if 'formulation_data' in selected_target_profile and selected_target_profile['formulation_data'] is not None:
                                    st.markdown("**Formulation Data:**")
                                    formulation_data = selected_target_profile['formulation_data']
                                    st.dataframe(formulation_data, use_container_width=True)
                                    
                                    # Show Type
                                    if 'Type' in formulation_data.columns:
                                        formulation_type = formulation_data.iloc[0]['Type']
                                        st.markdown(f"**Type:** {formulation_type}")
                                else:
                                    st.warning("⚠️ No Formulation data in this profile")
                    else:
                        st.warning(f"❌ No target profiles of type '{selected_type_filter}' found")
                        selected_target_profile_name = None
                else:
                    st.error("❌ No complete target profiles in current job")
                    st.info("💡 Create complete target profiles in 'Manage target profile' → 'Create target profile'")
                    selected_target_profile_name = None
            
            # Column 2: Model Selection
            with col_model:
                st.markdown("**Model Selection**")
                
                # Predefined model options
                model_options = [
                    "",
                    "MLP Model",
                    "Group Method Model", 
                    "GNN Model"
                ]
                
                selected_model = st.selectbox(
                    "Select Model:",
                    model_options,
                    key=f"{prefix}_model_select"
                )
                
                # Show model description based on selection
                if selected_model:
                    model_descriptions = {
                        "MLP Model": "Multi-Layer Perceptron neural network model for nonlinear pattern recognition",
                        "Group Method Model": "Group method of data handling for complex system modeling",
                        "GNN Model": "Graph Neural Network model for molecular structure analysis"
                    }
                    
                    with st.expander(f"ℹ️ About {selected_model}", expanded=False):
                        st.write(model_descriptions.get(selected_model, "Model description not available"))

            st.divider()

            # Calculate section
            st.subheader("Input Review and Submit Job")
            
            # Show selected target profile and model summary
            col_profile_summary, col_model_summary = st.columns(2)
            
            with col_profile_summary:
                st.markdown("**Selected Target Profile**")
                if selected_target_profile and selected_target_profile_name:
                    st.markdown(f"*{selected_target_profile_name}*")
                    
                    # Quick summary of profile components
                    api_status = "✅" if selected_target_profile.get('api_data') is not None else "❌"
                    polymer_status = "✅" if selected_target_profile.get('polymer_data') is not None else "❌"
                    formulation_status = "✅" if selected_target_profile.get('formulation_data') is not None else "❌"
                    
                    st.markdown(f"• API Data: {api_status}")
                    st.markdown(f"• Polymer Data: {polymer_status}")
                    st.markdown(f"• Formulation Data: {formulation_status}")
                    
                    # Show type if available
                    if (selected_target_profile.get('formulation_data') is not None and 
                        'Type' in selected_target_profile['formulation_data'].columns):
                        profile_type = selected_target_profile['formulation_data'].iloc[0]['Type']
                        st.markdown(f"• **Type:** {profile_type}")
                else:
                    selected_target_profile_name = None
            
            with col_model_summary:
                st.markdown("**Selected Model**")
                if selected_model:
                    st.markdown(f"*{selected_model}*")
                else:
                    selected_model = None
            
            # Submit button and Clear Results button
            has_target_profile = selected_target_profile is not None and selected_target_profile_name is not None
            has_model = selected_model is not None and selected_model != ""
            
            # Check if target profile is complete (has all three components)
            profile_complete = False
            if has_target_profile:
                api_ok = selected_target_profile.get('api_data') is not None
                polymer_ok = selected_target_profile.get('polymer_data') is not None
                formulation_ok = selected_target_profile.get('formulation_data') is not None
                profile_complete = api_ok and polymer_ok and formulation_ok
            
            can_submit = has_target_profile and has_model and profile_complete
            
            col_submit, col_clear = st.columns(2)
            
            with col_submit:
                if st.button("Submit Job", key=f"{prefix}_run", disabled=not can_submit):
                    if not can_submit:
                        if not has_target_profile:
                            st.error("Please select a target profile first.")
                        elif not profile_complete:
                            st.error("Selected target profile is incomplete. Please ensure it has API, Polymer, and Formulation data.")
                        elif not has_model:
                            st.error("Please select a model first.")
                        else:
                            st.error("Please ensure target profile and model are both selected before submitting.")
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
                        
                        # Get Release Time from target profile formulation data
                        release_time_value = 10  # Default fallback
                        if (selected_target_profile.get('formulation_data') is not None and 
                            len(selected_target_profile['formulation_data'].columns) >= 4):
                            formulation_data = selected_target_profile['formulation_data']
                            
                            # Find release time column
                            if 'Type' in formulation_data.columns:
                                data_columns = [col for col in formulation_data.columns if col not in ['Name', 'Type']]
                                if len(data_columns) >= 3:
                                    release_time_value = formulation_data.iloc[0][data_columns[2]]  # Third data column
                            else:
                                release_time_value = formulation_data.iloc[0, 3]  # Fourth column
                            
                            # Convert to numeric if it's a string with units
                            if isinstance(release_time_value, str):
                                release_time_value = float(release_time_value.replace('%', '').replace('Day', '').replace('Week', '').strip())
                            elif not isinstance(release_time_value, (int, float)):
                                release_time_value = float(release_time_value)
                        
                        # Generate fixed performance trend data for all 3 formulations
                        performance_trends = {}
                        x_points = 10
                        x_values = np.linspace(0, release_time_value, x_points).tolist()
                        
                        # Set seed for reproducible results within this job
                        np.random.seed(hash(current_job_name + selected_target_profile_name + selected_model) % 2147483647)
                        
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
                        np.random.seed(hash(current_job_name + selected_target_profile_name + selected_model + "evaluation") % 2147483647)
                        
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
                            "model_name": selected_model,
                            "selected_target_profile": selected_target_profile,
                            "selected_target_profile_name": selected_target_profile_name,
                            "target_type_filter": selected_type_filter if 'selected_type_filter' in locals() else "All",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "completed",
                            
                            # Generated result datasets
                            "composition_results": composition_results,
                            "performance_metrics": performance_metrics,
                            "performance_trends": performance_trends,
                            "evaluation_diagrams": evaluation_diagrams_data
                        }
                        
                        current_job.result_dataset = result_data
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Results generated using {selected_model} with target profile '{selected_target_profile_name}'")
            
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

    # Render each tab
    render_model_tab("atps", tab_atps)
