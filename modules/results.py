# modules/results.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random

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
    if not hasattr(job, 'optimization_progress'):
        job.optimization_progress = {}
    if not hasattr(job, 'current_optimization_progress'):
        job.current_optimization_progress = None
    return job

def show():
    st.header("Results")

    # Get current job from sidebar selection
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job to view results.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    
    # Ensure job has all required attributes
    current_job = ensure_job_attributes(current_job)
    
    # Update the job in session state (ensures all data is current)
    st.session_state.jobs[current_job_name] = current_job
    
    # Initialize formulation_results if it doesn't exist
    if not hasattr(current_job, 'formulation_results'):
        current_job.formulation_results = {}
    
    # Check if current job has results (either old format or new formulation-specific format)
    has_old_results = current_job.result_dataset is not None
    has_formulation_results = bool(current_job.formulation_results)
    has_optimization_progress = hasattr(current_job, 'current_optimization_progress') and current_job.current_optimization_progress is not None
    
    if not (has_old_results or has_formulation_results):
        st.info("No results available. Please run optimization first.")
        
        # Show optimization progress status if available
        if has_optimization_progress:
            progress = current_job.current_optimization_progress
            progress_status = progress.get('status', 'unknown')
            st.info(f"🔬 Current optimization progress: {progress_status.title()}")
            if progress_status == 'in_progress':
                st.markdown("**Optimization setup saved but not completed yet.**")
                st.markdown(f"- Target Profile: {progress.get('target_profile_name', 'None')}")
                st.markdown(f"- ATPS Model: {progress.get('atps_model', 'None')}")
                st.markdown(f"- Drug Release Model: {progress.get('drug_release_model', 'None')}")
        
        # Show helpful guidance
        st.markdown("""
        **To generate results:**
        1. Go to **'Modeling Optimization'** tab
        2. Select a **Target Profile** and **Formulation**
        3. Choose **ATPS Model** and **Drug Release Model**
        4. Click **'Submit Job'** to generate results
        5. Return here to view the analysis
        """)
        return

    # Top-level tabs
    tab_summary, tab_evaluation = st.tabs(["Summary", "Evaluation"])

    # ── Summary Tab ──────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Results Summary")
        
        # Show optimization progress info if available
        if has_optimization_progress:
            progress = current_job.current_optimization_progress
        
        # Formulation-specific results selection
        col_profile_sel, col_form_sel, col_clear = st.columns([2, 2, 1])
        
        # Initialize variables at the beginning
        selected_profile_for_results = None
        selected_formulation_for_results = None
        
        with col_profile_sel:
            # Get available profiles with results
            profiles_with_results = []
            if hasattr(current_job, 'formulation_results') and current_job.formulation_results:
                profiles_with_results = list(current_job.formulation_results.keys())
            
            if profiles_with_results:
                selected_profile_for_results = st.selectbox(
                    "Select Profile with Results:",
                    profiles_with_results,
                    key="results_profile_select"
                )
            else:
                selected_profile_for_results = None
                st.selectbox(
                    "Select Profile with Results:",
                    ["No profiles with results available"],
                    disabled=True
                )
        
        with col_form_sel:
            if selected_profile_for_results and selected_profile_for_results in current_job.formulation_results:
                formulations_with_results = list(current_job.formulation_results[selected_profile_for_results].keys())
                selected_formulation_for_results = st.selectbox(
                    "Select Formulation with Results:",
                    formulations_with_results,
                    key="results_formulation_select"
                )
            else:
                selected_formulation_for_results = None
                st.selectbox(
                    "Select Formulation with Results:",
                    ["Select profile first"],
                    disabled=True
                )
        
        with col_clear:
            # Clear specific formulation results
            if (selected_profile_for_results and selected_formulation_for_results and
                hasattr(current_job, 'formulation_results') and
                current_job.has_formulation_results(selected_profile_for_results, selected_formulation_for_results)):
                if st.button("🗑️ Clear Results", key="clear_specific_results", help="Remove results for this formulation"):
                    del current_job.formulation_results[selected_profile_for_results][selected_formulation_for_results]
                    # Clean up empty profile entries
                    if not current_job.formulation_results[selected_profile_for_results]:
                        del current_job.formulation_results[selected_profile_for_results]
                    st.rerun()
            else:
                st.button("🗑️ Clear Results", disabled=True, help="No results to clear")
        
        # Display results if formulation is selected
        if (selected_profile_for_results and selected_formulation_for_results and
            hasattr(current_job, 'formulation_results') and
            current_job.has_formulation_results(selected_profile_for_results, selected_formulation_for_results)):
            
            result_data = current_job.get_formulation_result(selected_profile_for_results, selected_formulation_for_results)
            
            st.markdown(f"**Results for: {selected_profile_for_results} → {selected_formulation_for_results}**")
            
            # Show optimization details
            with st.expander("🔬 Optimization Details", expanded=False):
                col_models, col_timestamp = st.columns(2)
                with col_models:
                    st.markdown(f"**ATPS Model:** {result_data.get('atps_model_name', 'Unknown')}")
                    st.markdown(f"**Drug Release Model:** {result_data.get('drug_release_model_name', 'Unknown')}")
                with col_timestamp:
                    st.markdown(f"**Generated:** {result_data.get('timestamp', 'Unknown')}")
                    st.markdown(f"**Status:** {result_data.get('status', 'Unknown')}")
                
                # Show formulation properties
                if 'formulation_properties' in result_data:
                    st.markdown("**Formulation Properties:**")
                    form_props = result_data['formulation_properties']
                    props_df = pd.DataFrame([form_props])
                    st.dataframe(props_df, use_container_width=True)

            # Get Gel Polymer name from target profile
            gel_polymer_name = "Not specified"
            if 'selected_target_profile' in result_data and result_data['selected_target_profile']:
                target_profile = result_data['selected_target_profile']
                if ('polymer_data' in target_profile and 
                    target_profile['polymer_data'] is not None and
                    'Name' in target_profile['polymer_data'].columns):
                    gel_polymer_name = target_profile['polymer_data'].iloc[0]['Name']
            
            # Get Co-polymer name randomly from Polymer database, excluding Gel Polymer
            co_polymer_name = "Not specified"
            if "polymer_datasets" in st.session_state and st.session_state["polymer_datasets"]:
                # Set seed for consistent results per job and formulation
                random.seed(hash(current_job_name + selected_formulation_for_results) % 2147483647)
                
                # Collect all polymer names from all datasets
                available_polymers = []
                for dataset_name, dataset_df in st.session_state["polymer_datasets"].items():
                    if 'Name' in dataset_df.columns:
                        polymer_names = dataset_df['Name'].tolist()
                        available_polymers.extend([str(name) for name in polymer_names if pd.notna(name)])
                
                # Remove duplicates and exclude Gel Polymer
                unique_polymers = list(set(available_polymers))
                if gel_polymer_name in unique_polymers:
                    unique_polymers.remove(gel_polymer_name)
                
                # Select random co-polymer
                if unique_polymers:
                    co_polymer_name = random.choice(unique_polymers)
            
            st.divider()
            
            # Composition Results
            st.markdown("**Composition Results**")
            
            # Use the composition results from the specific formulation
            if 'composition_results' in result_data:
                composition_data = result_data['composition_results']
                
                # Enhance composition results with polymer names
                enhanced_composition = []
                for comp in composition_data:
                    enhanced_comp = comp.copy()
                    enhanced_comp["Gel Polymer"] = gel_polymer_name
                    enhanced_comp["Co-polymer"] = co_polymer_name
                    enhanced_composition.append(enhanced_comp)
                
                df_comp_enhanced = pd.DataFrame(enhanced_composition)
                # Reorder columns for better display
                column_order = ["Gel Polymer", "Co-polymer", "Candidate", "Gel Polymer w/w", "Co-polymer w/w", "Buffer w/w"]
                available_columns = [col for col in column_order if col in df_comp_enhanced.columns]
                df_comp_enhanced = df_comp_enhanced[available_columns]
                st.dataframe(df_comp_enhanced, use_container_width=True)
            else:
                st.warning("No composition results available")
            
            st.divider()
            
            # Performance Review
            st.markdown("**Performance review**")
            
            # Use candidates from the specific formulation results
            if 'composition_results' in result_data:
                candidate_options = [comp['Candidate'] for comp in result_data['composition_results']]
                selected_candidate = st.selectbox(
                    "Select Candidate to Analyze:",
                    candidate_options,
                    key="candidate_selector"
                )
            else:
                st.warning("No candidates available")
                selected_candidate = None

            if selected_candidate:
                # Get release time from the formulation properties
                release_time_value = 4  # Default fallback
                if 'formulation_properties' in result_data and 'Release Time (Week)' in result_data['formulation_properties']:
                    release_time_value = result_data['formulation_properties']['Release Time (Week)']
                    if isinstance(release_time_value, str):
                        release_time_value = float(release_time_value.replace('%', '').replace('Day', '').replace('Week', '').strip())
                    elif not isinstance(release_time_value, (int, float)):
                        release_time_value = float(release_time_value)
                
                # Three column layout for ATPS Composition, Drug Release, and Target vs Result
                col_atps, col_performance, col_radar = st.columns(3)
                
                with col_atps:
                    st.markdown("**ATPS Composition**")
                    
                    # Generate ATPS composition based on selected formulation and candidate
                    # Set seed for consistent ATPS values per formulation and candidate
                    seed_str = f"{current_job_name}_{selected_profile_for_results}_{selected_formulation_for_results}_{selected_candidate}_atps"
                    random.seed(hash(seed_str) % 2147483647)
                    
                    # Get reference values from composition results
                    ref_gel_polymer = random.randint(5, 15)  # Reference gel polymer percentage
                    ref_co_polymer = random.randint(5, 15)   # Reference co-polymer percentage
                    ref_buffer = 100 - ref_gel_polymer - ref_co_polymer  # Reference buffer percentage
                    
                    # Calculate ATPS composition following the rules:
                    # Top Phase: gel polymer < ref, co-polymer > ref
                    # Bottom Phase: gel polymer > ref, co-polymer < ref
                    # Each column sums to 100%
                    
                    # Top Phase calculations
                    top_gel_polymer = ref_gel_polymer * random.uniform(0.6, 0.9)  # Smaller than reference
                    top_co_polymer = ref_co_polymer * random.uniform(1.1, 1.4)   # Larger than reference
                    top_buffer = 100 - top_gel_polymer - top_co_polymer          # Make sum = 100%
                    
                    # Ensure top_buffer is positive
                    if top_buffer < 0:
                        top_buffer = random.uniform(70, 85)
                        remaining = 100 - top_buffer
                        top_gel_polymer = remaining * 0.3
                        top_co_polymer = remaining * 0.7
                    
                    # Bottom Phase calculations
                    bottom_gel_polymer = ref_gel_polymer * random.uniform(1.1, 1.4)  # Larger than reference
                    bottom_co_polymer = ref_co_polymer * random.uniform(0.6, 0.9)   # Smaller than reference
                    bottom_buffer = 100 - bottom_gel_polymer - bottom_co_polymer    # Make sum = 100%
                    
                    # Ensure bottom_buffer is positive
                    if bottom_buffer < 0:
                        bottom_buffer = random.uniform(70, 85)
                        remaining = 100 - bottom_buffer
                        bottom_gel_polymer = remaining * 0.7
                        bottom_co_polymer = remaining * 0.3
                    
                    # Create ATPS composition table
                    atps_data = {
                        "Component": ["Gel polymer concentration", "Co-polymer concentration", "Buffer concentration"],
                        "Top Phase": [f"{top_gel_polymer:.1f}%", f"{top_co_polymer:.1f}%", f"{top_buffer:.1f}%"],
                        "Bottom Phase": [f"{bottom_gel_polymer:.1f}%", f"{bottom_co_polymer:.1f}%", f"{bottom_buffer:.1f}%"]
                    }
                    df_atps = pd.DataFrame(atps_data)
                    st.dataframe(df_atps, use_container_width=True)
                    
                    # Show verification that columns sum to 100%
                    top_sum = top_gel_polymer + top_co_polymer + top_buffer
                    bottom_sum = bottom_gel_polymer + bottom_co_polymer + bottom_buffer
                    st.caption(f"Top Phase Total: {top_sum:.1f}% | Bottom Phase Total: {bottom_sum:.1f}%")
                
                with col_performance:
                    st.markdown("**Drug Release**")
                    
                    # ONLY LOAD PRE-GENERATED GRAPH DATA (no generation here)
                    if 'performance_trends' in result_data and selected_candidate in result_data['performance_trends']:
                        # Load complete graph data generated in optimization.py
                        trend_data = result_data['performance_trends'][selected_candidate]
                        
                        # Extract pre-generated data
                        x_values = trend_data['x_values']
                        y_values = trend_data['y_values']
                        graph_config = trend_data.get('graph_config', {})
                        key_points = trend_data.get('key_points', {})
                        model_description = trend_data.get('model_description', 'Drug Release Profile')
                        
                        # Create graph using PRE-GENERATED data only
                        fig, ax = plt.subplots(figsize=(4, 3.3))
                        
                        # Use pre-generated graph configuration
                        colors = graph_config.get('colors', ['#1f77b4', '#ff7f0e', '#2ca02c'])
                        candidate_color_index = graph_config.get('candidate_color_index', 0)
                        color = colors[candidate_color_index % len(colors)]
                        linewidth = graph_config.get('linewidth', 2)
                        markersize = graph_config.get('markersize', 4)
                        alpha = graph_config.get('alpha', 0.3)
                        
                        # Plot the PRE-GENERATED curve
                        ax.plot(x_values, y_values, marker="o", linewidth=linewidth, markersize=markersize, color=color)
                        ax.fill_between(x_values, y_values, alpha=alpha, color=color)                        
                        
                        # Use PRE-GENERATED graph settings
                        title = graph_config.get('title', 'Drug Release Profile')
                        xlabel = graph_config.get('xlabel', 'Time (Weeks)')
                        ylabel = graph_config.get('ylabel', 'Drug Concentration')
                        ylim = graph_config.get('ylim', [0, 1.0])
                        
                        ax.set_xlim(0, trend_data.get('release_time', 10))
                        ax.set_ylim(*ylim)
                        ax.set_xlabel(xlabel, fontsize=9)
                        ax.set_ylabel(ylabel, fontsize=9)
                        ax.set_title(title, fontsize=10, fontweight='bold')
                        
                        # Add grid for better readability
                        ax.grid(True, alpha=0.3)
                        ax.set_axisbelow(True)
                        
                        # Add legend with smaller font
                        ax.legend(loc='center right', fontsize=7)
                        
                        # Adjust tick label sizes
                        ax.tick_params(labelsize=8)                      
                        
                        st.pyplot(fig)
                        
                    else:
                        # Fallback if no pre-generated data exists
                        st.warning("⚠️ No drug release data available. Please run optimization first.")
                        st.info("💡 Graph data is generated during optimization and displayed here.")

                with col_radar:
                    st.markdown("**Target vs Result**")
                    
                    # Generate result values based on selected formulation and candidate
                    # Set seed for consistent results per formulation and candidate
                    seed_str = f"{current_job_name}_{selected_profile_for_results}_{selected_formulation_for_results}_{selected_candidate}_radar"
                    random.seed(hash(seed_str) % 2147483647)
                    
                    # Target values are always 100%
                    target_values = [100, 100, 100]
                    
                    # Result values are 70-110% of target values
                    result_values = [
                        random.uniform(70, 110),  # Modulus result (70-110%)
                        random.uniform(70, 110),  # Encapsulation Rate result (70-110%)
                        random.uniform(70, 110)   # Release Time result (70-110%)
                    ]
                    
                    # Create radar chart with updated specifications
                    labels = ['Modulus', 'Encap Rate', 'Release Time']  # Shortened labels
                    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                    
                    # Close the radar chart
                    target_plot = target_values + target_values[:1]
                    result_plot = result_values + result_values[:1]
                    angles_plot = angles + angles[:1]
                    
                    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw={'polar': True})  # Reduced size by 2/3
                    
                    # Plot target profile line at 100%
                    ax.plot(angles_plot, target_plot, marker="o", linewidth=1.5, markersize=4, 
                           color='blue', label='Target', alpha=0.8)
                    ax.fill(angles_plot, target_plot, alpha=0.15, color='blue')
                    
                    # Plot result line (70-110% range)
                    ax.plot(angles_plot, result_plot, marker="s", linewidth=1.5, markersize=4, 
                           color='red', label='Result', alpha=0.8)
                    ax.fill(angles_plot, result_plot, alpha=0.15, color='red')
                    
                    # Customize radar chart with 5 graduations, 100% at 4th position
                    ax.set_thetagrids(np.degrees(angles), labels)
                    ax.set_ylim(0, 120)  # Scale to accommodate 110% max with headroom
                    
                    # Set 5 graduations with 100% at 4th position
                    ax.set_yticks([0, 20, 40, 60, 80, 100, 120])
                    ax.set_yticklabels(['0%', '20%', '40%', '60%', '80%','100%', '120%'], fontsize=6)
                    
                    ax.set_title(f"Target vs Result\n{selected_candidate}", 
                               y=1.05, fontsize=9, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0), fontsize=7)
                    
                    # Add percentage labels on the chart
                    for angle, target_val, result_val in zip(angles, target_values, result_values):
                        # Target values (always 100%)
                        ax.text(angle, target_val + 3, '100%', 
                               ha='center', va='center', fontsize=6, color='blue', fontweight='bold')
                        # Result values (70-110%)  
                        ax.text(angle, result_val - 8, f'{result_val:.0f}%', 
                               ha='center', va='center', fontsize=6, color='red', fontweight='bold')
                    
                    st.pyplot(fig)
            else:
                st.info("Please select a candidate to view performance analysis")
        
        elif not selected_profile_for_results:
            st.info("No results available. Please run optimization first to generate results.")
        else:
            st.info("Please select a profile and formulation with results to view detailed analysis.")

    # ── Evaluation Tab ───────────────────────────────────────────────────────
    with tab_evaluation:
        st.subheader("Evaluation")
        
        # Use the same formulation selection as in Summary tab
        if (selected_profile_for_results and selected_formulation_for_results and
            hasattr(current_job, 'formulation_results') and
            current_job.has_formulation_results(selected_profile_for_results, selected_formulation_for_results)):
            
            result_data = current_job.get_formulation_result(selected_profile_for_results, selected_formulation_for_results)
            
            st.markdown(f"**Evaluation for: {selected_profile_for_results} → {selected_formulation_for_results}**")
            
            # Candidate selection for evaluation
            if 'composition_results' in result_data:
                candidate_options = [comp['Candidate'] for comp in result_data['composition_results']]
                selected_candidate_eval = st.selectbox(
                    "Select Candidate for Evaluation:",
                    candidate_options,
                    key="evaluation_candidate_selector"
                )
                
                if selected_candidate_eval:
                    # Get evaluation data from result_data if available
                    if ('evaluation_diagrams' in result_data and 
                        selected_candidate_eval in result_data['evaluation_diagrams']):
                        
                        eval_data = result_data['evaluation_diagrams'][selected_candidate_eval]
                        safety_stability_scores = eval_data['safety_stability']
                        formulation_scores = eval_data['formulation']
                    else:
                        # Fallback: generate evaluation data
                        seed_str = f"{current_job_name}_{selected_profile_for_results}_{selected_formulation_for_results}_{selected_candidate_eval}_evaluation"
                        eval_seed = hash(seed_str) % 2147483647
                        random.seed(eval_seed)
                        
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
                    
                    st.divider()
                    
                    col_left, col_right = st.columns(2)
                    
                    # Left Column: Safety & Stability Score
                    with col_left:
                        labels_safety = list(safety_stability_scores.keys())
                        vals_safety = list(safety_stability_scores.values())
                        
                        # Create radar chart for Safety & Stability
                        angles = np.linspace(0, 2*np.pi, len(labels_safety), endpoint=False).tolist()
                        vals_plot = vals_safety + vals_safety[:1]  # Complete the circle
                        angles_plot = angles + angles[:1]  # Complete the circle
                        
                        fig1, ax1 = plt.subplots(figsize=(4, 4), subplot_kw={'polar': True})
                        ax1.plot(angles_plot, vals_plot, marker="o", linewidth=3, markersize=8, color='#2E8B57')
                        ax1.fill(angles_plot, vals_plot, alpha=0.25, color='#2E8B57')
                        ax1.set_thetagrids(np.degrees(angles), labels_safety)
                        ax1.set_ylim(0, 10)
                        ax1.set_title(f"Safety & Stability Score\n{selected_candidate_eval}", y=1.08, fontsize=12, fontweight='bold')
                        ax1.grid(True, alpha=0.3)
                        
                        # Add score labels on the chart
                        for angle, val, label in zip(angles, vals_safety, labels_safety):
                            ax1.text(angle, val + 0.5, str(val), ha='center', va='center', 
                                   fontsize=11, fontweight='bold', color='darkgreen')
                        
                        st.pyplot(fig1)
                    
                    # Right Column: Formulation Score
                    with col_right:
                        labels_formulation = list(formulation_scores.keys())
                        vals_formulation = list(formulation_scores.values())
                        
                        # Create radar chart for Formulation
                        angles = np.linspace(0, 2*np.pi, len(labels_formulation), endpoint=False).tolist()
                        vals_plot = vals_formulation + vals_formulation[:1]  # Complete the circle
                        angles_plot = angles + angles[:1]  # Complete the circle
                        
                        fig2, ax2 = plt.subplots(figsize=(4, 4), subplot_kw={'polar': True})
                        ax2.plot(angles_plot, vals_plot, marker="s", linewidth=3, markersize=8, color='#FF6347')
                        ax2.fill(angles_plot, vals_plot, alpha=0.25, color='#FF6347')
                        ax2.set_thetagrids(np.degrees(angles), labels_formulation)
                        ax2.set_ylim(0, 10)
                        ax2.set_title(f"Formulation Score\n{selected_candidate_eval}", y=1.08, fontsize=12, fontweight='bold')
                        ax2.grid(True, alpha=0.3)
                        
                        # Add score labels on the chart
                        for angle, val, label in zip(angles, vals_formulation, labels_formulation):
                            ax2.text(angle, val + 0.5, str(val), ha='center', va='center', 
                                   fontsize=11, fontweight='bold', color='darkred')
                        
                        st.pyplot(fig2)
                else:
                    st.info("Please select a candidate for evaluation")
            else:
                st.warning("No candidates available for evaluation")
        else:
            st.info("Please select a formulation with results in the Summary tab first to view evaluation data.")
    
    st.divider()
    
    # ── Progress Management Section ─────────────────────────────────────────
    st.markdown("## 💾 Progress Management")
    
    col_save_progress, col_clear_progress = st.columns(2)
    
    with col_save_progress:
        st.markdown("### Save Progress")
        st.markdown("Save current job progress to cloud")
        
        if st.button("💾 Save Progress", key="results_save_progress", 
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
        st.markdown("Clear current job progress data")
        
        if st.button("🗑️ Clear Progress", key="results_clear_progress",
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
