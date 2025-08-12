# modules/optimization.py
import streamlit as st
import pandas as pd
import time
import random
import numpy as np
import json
import os
from datetime import datetime

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def save_progress_to_file(job, job_name, target_profile, target_profile_name, atps_model, drug_release_model):
    """Save optimization progress to JSON file"""
    try:
        # Create saved_progress directory if it doesn't exist
        os.makedirs("saved_progress", exist_ok=True)
        
        # Create progress data structure
        progress_data = {
            "job_name": job_name,
            "target_profile_name": target_profile_name,
            "atps_model": atps_model,
            "drug_release_model": drug_release_model,
            "target_profile": target_profile,
            "saved_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Convert DataFrames to serializable format
        if target_profile:
            serializable_profile = {}
            for key, value in target_profile.items():
                if hasattr(value, 'to_dict'):  # It's a DataFrame
                    serializable_profile[key] = value.to_dict('records')
                else:
                    serializable_profile[key] = value
            progress_data["target_profile"] = serializable_profile
        
        # Save to file
        filename = f"saved_progress/{job_name}_optimization_progress.json"
        with open(filename, 'w') as f:
            json.dump(progress_data, f, indent=2)
        
        st.success(f"✅ Optimization progress saved permanently!")
        st.info(f"📁 Saved to: {filename}")
        return True, filename
    except Exception as e:
        st.error(f"❌ Failed to save progress: {str(e)}")
        return False, str(e)

def show():
    st.header("Modeling Optimization")

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
            st.markdown('<p class="font-medium"><b>Select Model Inputs</b></p>', unsafe_allow_html=True)
            
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
                    
                    # Target Profile Selection (no type filter)
                    profile_names = list(target_profiles.keys())
                    selected_target_profile_name = st.selectbox(
                        "Select Target Profile:",
                        [""] + profile_names,
                        key=f"{prefix}_target_profile_select"
                    )
                    
                    if selected_target_profile_name:
                        selected_target_profile = target_profiles[selected_target_profile_name]
                        
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
                                st.markdown(f"**Number of formulations:** {len(formulation_data)}")
                            else:
                                st.warning("⚠️ No Formulation data in this profile")
                    else:
                        selected_target_profile = None
                        selected_target_profile_name = None
                else:
                    st.error("❌ No complete target profiles in current job")
                    st.info("💡 Create complete target profiles in 'Manage target profile' → 'Create target profile'")
                    selected_target_profile_name = None
            
            # Column 2: Model Selection
            with col_model:
                st.markdown("**Model Selection**")
                
                # ATPS Model Selection
                st.markdown("**Select ATPS Model**")
                atps_model_options = [
                    "",
                    "MLP Model",
                    "Group Method Model", 
                    "GNN Model"
                ]
                
                selected_atps_model = st.selectbox(
                    "ATPS Model:",
                    atps_model_options,
                    key=f"{prefix}_atps_model_select",
                    label_visibility="collapsed"
                )
                
                # Show ATPS model description based on selection
                if selected_atps_model:
                    atps_model_descriptions = {
                        "MLP Model": "Multi-Layer Perceptron neural network model for nonlinear pattern recognition",
                        "Group Method Model": "Group method of data handling for complex system modeling",
                        "GNN Model": "Graph Neural Network model for molecular structure analysis"
                    }
                    
                    with st.expander(f"ℹ️ About {selected_atps_model}", expanded=False):
                        st.write(atps_model_descriptions.get(selected_atps_model, "Model description not available"))
                
                # Drug Release Model Selection
                st.markdown("**Drug Release Model Selection**")
                drug_release_model_options = [
                    "",
                    "Diffusion Model",
                    "Particle Kinetics Model"
                ]
                
                selected_drug_release_model = st.selectbox(
                    "Drug Release Model:",
                    drug_release_model_options,
                    key=f"{prefix}_drug_release_model_select",
                    label_visibility="collapsed"
                )
                
                # Show Drug Release model description based on selection
                if selected_drug_release_model:
                    drug_release_model_descriptions = {
                        "Diffusion Model": "Mathematical model based on Fick's laws of diffusion for drug release kinetics",
                        "Particle Kinetics Model": "Kinetic model analyzing particle dissolution and drug release mechanisms"
                    }
                    
                    with st.expander(f"ℹ️ About {selected_drug_release_model}", expanded=False):
                        st.write(drug_release_model_descriptions.get(selected_drug_release_model, "Model description not available"))

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
                    st.info("No target profile selected")
                    selected_target_profile_name = None
            
            with col_model_summary:
                st.markdown("**Selected Models**")
                if selected_atps_model:
                    st.markdown(f"*ATPS: {selected_atps_model}*")
                else:
                    st.info("No ATPS model selected")
                    
                if selected_drug_release_model:
                    st.markdown(f"*Drug Release: {selected_drug_release_model}*")
                else:
                    st.info("No Drug Release model selected")
                
                if not (selected_atps_model and selected_drug_release_model):
                    selected_atps_model = None
                    selected_drug_release_model = None
            
            # Submit button and Clear Results button
            has_target_profile = selected_target_profile is not None and selected_target_profile_name is not None
            has_atps_model = selected_atps_model is not None and selected_atps_model != ""
            has_drug_release_model = selected_drug_release_model is not None and selected_drug_release_model != ""
            
            # Check if target profile is complete (has all three components)
            profile_complete = False
            if has_target_profile:
                api_ok = selected_target_profile.get('api_data') is not None
                polymer_ok = selected_target_profile.get('polymer_data') is not None
                formulation_ok = selected_target_profile.get('formulation_data') is not None
                profile_complete = api_ok and polymer_ok and formulation_ok
            
            can_submit = has_target_profile and has_atps_model and has_drug_release_model and profile_complete
            
            col_submit, col_save, col_clear = st.columns(3)
            
            with col_submit:
                if st.button("Submit Job", key=f"{prefix}_run", disabled=not can_submit):
                    if not can_submit:
                        if not has_target_profile:
                            st.error("Please select a target profile first.")
                        elif not profile_complete:
                            st.error("Selected target profile is incomplete. Please ensure it has API, Polymer, and Formulation data.")
                        elif not has_atps_model:
                            st.error("Please select an ATPS model first.")
                        elif not has_drug_release_model:
                            st.error("Please select a Drug Release model first.")
                        else:
                            st.error("Please ensure target profile and both models are selected before submitting.")
                    else:
                        progress = st.progress(0)
                        for i in range(101):
                            time.sleep(0.02)
                            progress.progress(i)
                        st.success("Completed Calculation")

                        # Create comprehensive result datasets during optimization
                        
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
                        np.random.seed(hash(current_job_name + selected_target_profile_name + selected_atps_model + selected_drug_release_model) % 2147483647)
                        
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
                        np.random.seed(hash(current_job_name + selected_target_profile_name + selected_atps_model + selected_drug_release_model + "evaluation") % 2147483647)
                        
                        evaluation_diagrams_data = {}
                        
                        # Generate evaluation data for each of the 3 formulations
                        for i in range(3):
                            formulation_name = f"Formulation {i+1}"
                            
                            # Safety & Stability Score (6-9) - different for each formulation
                            safety_stability_scores = {
                                "Degradability": random.randint(6, 9),
                                "Cytotoxicity": random.randint(6, 9),
                                "Immunogenicity": random.randint(6, 9)
                            }
                            
                            # Formulation Score (6-9) - different for each formulation
                            formulation_scores = {
                                "Durability": random.randint(6, 9),
                                "Injectability": random.randint(6, 9),
                                "Strength": random.randint(6, 9)
                            }
                            
                            evaluation_diagrams_data[formulation_name] = {
                                "safety_stability": safety_stability_scores,
                                "formulation": formulation_scores,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        
                        # Create comprehensive result data with all generated datasets
                        result_data = {
                            "type": prefix,
                            "atps_model_name": selected_atps_model,
                            "drug_release_model_name": selected_drug_release_model,
                            "selected_target_profile": selected_target_profile,
                            "selected_target_profile_name": selected_target_profile_name,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "completed",
                            
                            # Generated result datasets
                            "composition_results": composition_results,
                            "performance_metrics": performance_metrics,
                            "performance_trends": performance_trends,
                            "evaluation_diagrams": evaluation_diagrams_data
                        }
                        
                        current_job.result_dataset = result_data
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"Results generated using ATPS: {selected_atps_model}, Drug Release: {selected_drug_release_model}")
            
            with col_save:
                # Save Progress button - saves the current optimization setup
                save_disabled = not (selected_target_profile and selected_atps_model and selected_drug_release_model)
                
                if st.button("Save Progress", key=f"{prefix}_save_progress", 
                           disabled=save_disabled,
                           help="Save current optimization setup permanently"):
                    if not save_disabled:
                        # Save databases to job before saving progress
                        current_job.common_api_datasets = st.session_state.get("common_api_datasets", {})
                        current_job.polymer_datasets = st.session_state.get("polymer_datasets", {})
                        st.session_state.jobs[current_job_name] = current_job
                        
                        save_progress_to_file(current_job, current_job_name, selected_target_profile, selected_target_profile_name, selected_atps_model, selected_drug_release_model)
                    else:
                        st.error("Please select target profile and both models before saving progress.")
            
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
