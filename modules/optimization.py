# modules/optimization.py
import streamlit as st
import pandas as pd
import time
import random
import numpy as np
from datetime import datetime

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

# Import unified storage functions
try:
    from modules.storage_utils import save_progress_to_job, clear_progress_from_job
except ImportError:
    # Fallback if storage_utils not available yet
    def save_progress_to_job(job):
        return False, "Storage utilities not available"
    def clear_progress_from_job(job):
        return False, "Storage utilities not available"

def ensure_job_attributes(job):
    """Ensure all required attributes exist on a job object"""
    if not hasattr(job, 'common_api_datasets'):
        job.common_api_datasets = {}
    if not hasattr(job, 'polymer_datasets'):
        job.polymer_datasets = {}
    if not hasattr(job, 'complete_target_profiles'):
        job.complete_target_profiles = {}
    if not hasattr(job, 'formulation_results'):
        job.formulation_results = {}
    # NEW: Ensure optimization progress attributes exist
    if not hasattr(job, 'optimization_progress'):
        job.optimization_progress = {}
    if not hasattr(job, 'current_optimization_progress'):
        job.current_optimization_progress = None
    return job

def save_optimization_selections_to_job(current_job, target_profile_name, atps_model, drug_release_model):
    """Save current optimization selections to job for persistence"""
    # Ensure attributes exist
    if not hasattr(current_job, 'current_optimization_progress'):
        current_job.current_optimization_progress = None
    
    progress_data = {
        "target_profile_name": target_profile_name,
        "atps_model": atps_model,
        "drug_release_model": drug_release_model,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "in_progress"
    }
    current_job.current_optimization_progress = progress_data
    
    # FORCE IMMEDIATE SAVE to session state jobs
    if st.session_state.get("current_job"):
        st.session_state.jobs[st.session_state.current_job] = current_job

def get_saved_optimization_selections(current_job):
    """Get saved optimization selections from job"""
    # Ensure attributes exist
    if not hasattr(current_job, 'current_optimization_progress'):
        current_job.current_optimization_progress = None
    
    progress = current_job.current_optimization_progress
    if progress:
        return (
            progress.get("target_profile_name", ""),
            progress.get("atps_model", ""),
            progress.get("drug_release_model", "")
        )
    return "", "", ""

def clear_optimization_progress(current_job):
    """Clear current optimization progress"""
    if hasattr(current_job, 'current_optimization_progress'):
        current_job.current_optimization_progress = None

def has_optimization_progress(current_job):
    """Check if there is saved optimization progress"""
    if hasattr(current_job, 'current_optimization_progress'):
        return current_job.current_optimization_progress is not None
    return False

def show():
    st.header("Modeling Optimization")

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    
    # Ensure job has all required attributes
    current_job = ensure_job_attributes(current_job)
    
    # Update the job in session state (ensures all data is current)
    st.session_state.jobs[current_job_name] = current_job

    # Get saved optimization selections for persistence across page changes
    saved_target_profile, saved_atps_model, saved_drug_release_model = get_saved_optimization_selections(current_job)
    
    # # DEBUG: Show optimization progress data state
    # with st.expander("🔍 Debug Optimization Data", expanded=False):
    #     st.write(f"**Job Name:** {current_job.name}")
    #     st.write(f"**Target Profiles Available:** {len(current_job.complete_target_profiles)}")
    #     if current_job.complete_target_profiles:
    #         st.write(f"**Available Profiles:** {list(current_job.complete_target_profiles.keys())}")
    #     st.write(f"**Saved Optimization Progress:** {'Yes' if current_job.current_optimization_progress else 'No'}")
    #     if current_job.current_optimization_progress:
    #         st.json(current_job.current_optimization_progress)
    #     st.write(f"**Retrieved Saved Selections:** Target='{saved_target_profile}', ATPS='{saved_atps_model}', Drug='{saved_drug_release_model}'")

    # Top-level tabs
    tab_atps = st.tabs(["ATPS Partition"])[0]

    def render_model_tab(prefix, tab):
        with tab:
            # Two-column layout: Target Profile Selection + Model Selection
            st.markdown('<p class="font-medium"><b>Select Model Inputs</b></p>', unsafe_allow_html=True)
            
            col_target, col_model = st.columns([2, 1])
            
            # Column 1: Target Profile Selection
            with col_target:
                st.markdown("**Target Profile Selection**")
                
                # Initialize selection variables
                selected_target_profile = None
                selected_target_profile_name = None
                
                # Check if job has complete target profiles
                if hasattr(current_job, 'complete_target_profiles') and current_job.complete_target_profiles:
                    target_profiles = current_job.complete_target_profiles
                    
                    # Target Profile Selection with saved state restoration
                    profile_names = list(target_profiles.keys())
                    
                    # Find index of saved selection
                    saved_index = 0
                    if saved_target_profile and saved_target_profile in profile_names:
                        saved_index = profile_names.index(saved_target_profile) + 1  # +1 for empty option
                    
                    selected_target_profile_name = st.selectbox(
                        "Select Target Profile:",
                        [""] + profile_names,
                        index=saved_index,
                        key=f"{prefix}_target_profile_select"
                    )
                    
                    # Save selection when it changes
                    if selected_target_profile_name != saved_target_profile:
                        # Get current model selections to preserve them
                        current_atps = st.session_state.get(f"{prefix}_atps_model_select", saved_atps_model)
                        current_drug_release = st.session_state.get(f"{prefix}_drug_release_model_select", saved_drug_release_model)
                        save_optimization_selections_to_job(current_job, selected_target_profile_name, current_atps, current_drug_release)
                    
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
                                formulation_count = len(formulation_data)
                                st.markdown(f"**Number of formulations:** {formulation_count}")
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
                
                # ATPS Model Selection with saved state restoration
                st.markdown("**Select ATPS Model**")
                atps_model_options = [
                    "",
                    "MLP Model",
                    "Group Method Model", 
                    "GNN Model"
                ]
                
                # Find index of saved ATPS model
                atps_saved_index = 0
                if saved_atps_model and saved_atps_model in atps_model_options:
                    atps_saved_index = atps_model_options.index(saved_atps_model)
                
                selected_atps_model = st.selectbox(
                    "ATPS Model:",
                    atps_model_options,
                    index=atps_saved_index,
                    key=f"{prefix}_atps_model_select",
                    label_visibility="collapsed"
                )
                
                # Save ATPS model selection when it changes
                if selected_atps_model != saved_atps_model:
                    # Get current selections to preserve them
                    current_target = selected_target_profile_name if selected_target_profile_name else saved_target_profile
                    current_drug_release = st.session_state.get(f"{prefix}_drug_release_model_select", saved_drug_release_model)
                    save_optimization_selections_to_job(current_job, current_target, selected_atps_model, current_drug_release)
                
                # Drug Release Model Selection with saved state restoration
                st.markdown("**Drug Release Model Selection**")
                drug_release_model_options = [
                    "",
                    "Diffusion Model",
                    "Particle Kinetics Model"
                ]
                
                # Find index of saved Drug Release model
                drug_saved_index = 0
                if saved_drug_release_model and saved_drug_release_model in drug_release_model_options:
                    drug_saved_index = drug_release_model_options.index(saved_drug_release_model)
                
                selected_drug_release_model = st.selectbox(
                    "Drug Release Model:",
                    drug_release_model_options,
                    index=drug_saved_index,
                    key=f"{prefix}_drug_release_model_select",
                    label_visibility="collapsed"
                )
                
                # Save Drug Release model selection when it changes
                if selected_drug_release_model != saved_drug_release_model:
                    # Get current selections to preserve them
                    current_target = selected_target_profile_name if selected_target_profile_name else saved_target_profile
                    current_atps = selected_atps_model if selected_atps_model else saved_atps_model
                    save_optimization_selections_to_job(current_job, current_target, current_atps, selected_drug_release_model)

            st.divider()

            # Calculate section
            st.subheader("Input Review and Submit Job")           
            
            # # Debug section (can be removed later)
            # with st.expander("🔍 Debug Optimization Progress", expanded=False):
            #     if current_job.current_optimization_progress:
            #         st.write("**Current Optimization Progress:**")
            #         st.json(current_job.current_optimization_progress)
            #     else:
            #         st.write("No optimization progress saved yet")
                
            #     # Manual test save button
            #     if st.button("🧪 Test Save Progress", key="test_save_progress"):
            #         test_progress = {
            #             "target_profile_name": "Test Profile",
            #             "atps_model": "Test ATPS Model", 
            #             "drug_release_model": "Test Drug Release Model",
            #             "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #             "status": "test"
            #         }
            #         current_job.current_optimization_progress = test_progress
            #         st.session_state.jobs[current_job_name] = current_job
            #         st.success("Test progress saved!")
            
            # Show selected target profile and model summary
            col_profile_summary, col_model_summary = st.columns(2)
            
            with col_profile_summary:
                st.markdown("**Selected Target Profile**")
                if selected_target_profile and selected_target_profile_name:
                    
                    # Quick summary of profile components
                    api_status = "✅" if selected_target_profile.get('api_data') is not None else "❌"
                    polymer_status = "✅" if selected_target_profile.get('polymer_data') is not None else "❌"
                    formulation_status = "✅" if selected_target_profile.get('formulation_data') is not None else "❌"
                    
                    st.markdown(f"• API Data: {api_status}")
                    st.markdown(f"• Polymer Data: {polymer_status}")
                    st.markdown(f"• Formulation Data: {formulation_status}")

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
            
            col_submit, col_clear = st.columns(2)
            
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
                        # Show progress bar
                        progress = st.progress(0)
                        for i in range(101):
                            time.sleep(0.02)
                            progress.progress(i)
                        
                        # Get all formulations from the selected profile
                        formulation_data = selected_target_profile['formulation_data']
                        formulation_count = len(formulation_data)
                        
                        # Process each formulation and generate results
                        for idx, (_, formulation_row) in enumerate(formulation_data.iterrows()):
                            formulation_name = formulation_row.get('Name', f'Formulation_{idx+1}')
                            
                            # Generate composition results for this formulation
                            composition_results = []
                            for i in range(3):  # Create 3 candidates
                                buffer_pct = random.randint(80, 95)  # Buffer between 80-95%
                                remaining_pct = 100 - buffer_pct
                                
                                # Distribute remaining percentage between Gel Polymer and Co-polymer
                                gel_polymer_pct = random.randint(1, remaining_pct - 1)
                                co_polymer_pct = remaining_pct - gel_polymer_pct
                                
                                composition_results.append({
                                    "Candidate": f"Candidate {i+1}",
                                    "Gel Polymer w/w": f"{gel_polymer_pct}%",
                                    "Co-polymer w/w": f"{co_polymer_pct}%", 
                                    "Buffer w/w": f"{buffer_pct}%"
                                })
                            
                            # Generate performance metrics specific to this formulation
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
                            
                            # Get release time value for performance trends
                            release_time_value = 10  # Default fallback
                            if 'Release Time (Week)' in formulation_row:
                                release_time_value = formulation_row['Release Time (Week)']
                                if isinstance(release_time_value, str):
                                    release_time_value = float(release_time_value.replace('%', '').replace('Day', '').replace('Week', '').strip())
                                elif not isinstance(release_time_value, (int, float)):
                                    release_time_value = float(release_time_value)
                            
                            # Generate performance trend data for 3 candidates
                            performance_trends = {}
                            x_points = 10
                            x_values = np.linspace(0, release_time_value, x_points).tolist()
                            
                            start_values = [0.1, 0.15, 0.08]
                            end_values = [0.85, 0.92, 0.88]
                            
                            for i in range(3):
                                candidate_name = f"Candidate {i+1}"
                                base_trend = np.linspace(start_values[i], end_values[i], x_points)
                                noise = np.random.normal(0, 0.02, x_points)
                                y_values = base_trend + noise
                                
                                # Ensure values stay within 0-1 range and maintain upward trend
                                y_values = np.clip(y_values, 0, 1)
                                y_values = np.sort(y_values)  # Force upward trend
                                
                                performance_trends[candidate_name] = {
                                    "x_values": x_values,
                                    "y_values": y_values.tolist(),
                                    "release_time": release_time_value
                                }
                            
                            # Generate evaluation diagrams data for each candidate
                            evaluation_diagrams_data = {}
                            
                            for i in range(3):
                                candidate_name = f"Candidate {i+1}"
                                
                                # Safety & Stability Score (6-9) - different for each candidate
                                safety_stability_scores = {
                                    "Degradability": random.randint(6, 9),
                                    "Cytotoxicity": random.randint(6, 9),
                                    "Immunogenicity": random.randint(6, 9)
                                }
                                
                                # Formulation Score (6-9) - different for each candidate
                                formulation_scores = {
                                    "Durability": random.randint(6, 9),
                                    "Injectability": random.randint(6, 9),
                                    "Strength": random.randint(6, 9)
                                }
                                
                                evaluation_diagrams_data[candidate_name] = {
                                    "safety_stability": safety_stability_scores,
                                    "formulation": formulation_scores,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                            
                            # Create formulation-specific result data
                            formulation_result_data = {
                                "type": prefix,
                                "atps_model_name": selected_atps_model,
                                "drug_release_model_name": selected_drug_release_model,
                                "selected_target_profile": selected_target_profile,
                                "selected_target_profile_name": selected_target_profile_name,
                                "formulation_properties": formulation_row.to_dict(),
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "completed",
                                
                                # Generated result datasets specific to this formulation
                                "composition_results": composition_results,
                                "performance_metrics": performance_metrics,
                                "performance_trends": performance_trends,
                                "evaluation_diagrams": evaluation_diagrams_data
                            }
                            
                            # Save results at formulation level in job class
                            if not hasattr(current_job, 'formulation_results'):
                                current_job.formulation_results = {}
                            
                            current_job.set_formulation_result(selected_target_profile_name, formulation_name, formulation_result_data)
                        
                        # Update optimization progress to mark as completed with results
                        if hasattr(current_job, 'current_optimization_progress') and current_job.current_optimization_progress:
                            current_job.current_optimization_progress["status"] = "completed"
                            current_job.current_optimization_progress["results_generated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            current_job.current_optimization_progress["formulation_count"] = formulation_count
                        
                        # Ensure the job is updated in session state for persistence
                        st.session_state.jobs[current_job_name] = current_job
                        
                        # Optional: Auto-switch to results tab
                        if st.button("🔍 View Results Now", key="auto_switch_to_results"):
                            st.session_state.current_tab = "Show Results"
                            st.rerun()
            
            with col_clear:
                # # Clear Results button - clear all results for the selected profile or all results
                # has_any_results = current_job.has_result_data()
                # has_current_profile_results = (selected_target_profile_name and 
                #                              hasattr(current_job, 'formulation_results') and
                #                              selected_target_profile_name in current_job.formulation_results)
                
                clear_options = []
                # if has_current_profile_results:
                #     formulation_count = len(current_job.formulation_results[selected_target_profile_name])
                #     clear_options.append(f"Clear '{selected_target_profile_name}' Results ({formulation_count} formulations)")
                # if has_any_results:
                #     clear_options.append("Clear All Results")
                # if has_optimization_progress(current_job):
                #     clear_options.append("Clear Optimization Progress")
                
                # if clear_options:
                #     clear_choice = st.selectbox(
                #         "Clear Options:",
                #         [""] + clear_options,
                #         key=f"{prefix}_clear_choice"
                #     )
                    
                #     if clear_choice and st.button("🗑️ Clear Results", key=f"{prefix}_clear_results"):
                #         if clear_choice.startswith("Clear All"):
                #             # Clear all results
                #             current_job.result_dataset = None
                #             if hasattr(current_job, 'formulation_results'):
                #                 current_job.formulation_results = {}
                #         elif clear_choice.startswith("Clear Optimization"):
                #             # Clear optimization progress
                #             clear_optimization_progress(current_job)
                #         elif clear_choice.startswith("Clear") and selected_target_profile_name:
                #             # Clear all formulation results for the selected profile
                #             if (hasattr(current_job, 'formulation_results') and
                #                 selected_target_profile_name in current_job.formulation_results):
                #                 formulation_count = len(current_job.formulation_results[selected_target_profile_name])
                #                 del current_job.formulation_results[selected_target_profile_name]
                        
                #         st.session_state.jobs[current_job_name] = current_job
                #         st.rerun()
                # else:
                #     st.button("🗑️ Clear Results", disabled=True, help="No results to clear")

    # Render each tab
    render_model_tab("atps", tab_atps)
    
    st.divider()
    
    # ── Progress Management Section ─────────────────────────────────────────
    st.markdown("## 💾 Progress Management")
    
    col_save_progress, col_clear_progress = st.columns(2)
    
    with col_save_progress:
        st.markdown("### Save Progress")
        st.markdown("Save current job progress to cloud")
        
        if st.button("💾 Save Progress", key="optimization_save_progress", 
                   disabled=not current_job,
                   help="Save current progress to cloud"):
            if current_job:
                success, result = save_progress_to_job(current_job)
                if success:
                    st.success(f"✅ Progress saved successfully!")
                else:
                    st.error(f"❌ Failed to save progress: {result}")
            else:
                st.error("❌ No current job to save!")
    
    with col_clear_progress:
        st.markdown("### Clear Progress")
        st.markdown("Clear current job progress")
        
        if st.button("🗑️ Clear Progress", key="optimization_clear_progress",
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
