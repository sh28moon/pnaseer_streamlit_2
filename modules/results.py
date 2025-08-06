# modules/results.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.header("Results")

    # Get current job from sidebar selection
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    
    # Check if current job has results
    if not current_job.has_result_data():
        st.warning("⚠️ No completed jobs with results available. Please run optimization first.")
        return

    # Top-level tabs
    tab_summary, tab_evaluation = st.tabs(["Summary", "Evaluation"])

    # ── Summary Tab ──────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Results Summary")
        st.info(f"📁 Showing fixed results for job: **{current_job_name}**")
        
        result_data = current_job.result_dataset
        st.divider()
        
        # 1st Row: Summary Table
        st.markdown("**Job Summary**")
        
        # Create summary data
        summary_data = {
            "Job Name": [current_job_name],
            "Model Used": [result_data.get('model_name', 'Unknown')],
            "API Data": [result_data.get('selected_api_name', 'Unknown')],
            "Target Profile": [result_data.get('selected_target_name', 'Unknown')],
            "Completion Time": [result_data.get('timestamp', 'Unknown')],
            "Status": [result_data.get('status', 'Unknown').capitalize()]
        }
        
        df_summary = pd.DataFrame(summary_data)
        st.table(df_summary)
        
        st.divider()
        
        # 2nd Row: Composition Results with Clear Button
        col_comp, col_clear = st.columns([4, 1])
        with col_comp:
            st.markdown("**Composition Results**")
        with col_clear:
            if st.button("🗑️ Clear Results", key="clear_current_results", help="Remove results from current job"):
                current_job.result_dataset = None
                st.success(f"Results cleared from job '{current_job_name}'")
                st.rerun()
        
        # Use pre-generated composition results from optimization
        if 'composition_results' in result_data:
            comp_data_list = result_data['composition_results']
            df_comp = pd.DataFrame(comp_data_list)
            st.dataframe(df_comp, use_container_width=True)
        else:
            st.warning("No composition results found. Please re-run optimization.")
        
        st.divider()
        
        # 3rd Row: Single Performance Trend Graph with Composition Selector
        st.markdown("**Performance Trend Analysis**")
        
        # Use pre-generated performance trend data from optimization
        if 'performance_trends' in result_data:
            performance_trends = result_data['performance_trends']
            
            # Composition selector
            col_selector, col_graph = st.columns([1, 3])
            
            with col_selector:
                st.markdown("**Select Formulation**")
                formulation_options = list(performance_trends.keys())
                selected_formulation = st.selectbox(
                    "Choose formulation to analyze:",
                    formulation_options,
                    key="formulation_selector"
                )
                
                # Show composition data for selected formulation
                if 'composition_results' in result_data:
                    comp_data_list = result_data['composition_results']
                    # Find the composition data for selected formulation
                    selected_comp = None
                    for comp in comp_data_list:
                        if comp.get("Row") == selected_formulation:
                            selected_comp = comp
                            break
                    
                    if selected_comp:
                        st.markdown(f"**{selected_formulation} Composition:**")
                        for key, value in selected_comp.items():
                            if key != "Row":  # Skip the row identifier
                                st.write(f"• {key}: {value}")
            
            with col_graph:
                st.markdown(f"**Performance Trend - {selected_formulation}**")
                
                # Get pre-generated performance trend data for selected formulation
                if selected_formulation in performance_trends:
                    trend_data = performance_trends[selected_formulation]
                    x_values = trend_data["x_values"]
                    y_values = trend_data["y_values"]
                    release_time_value = trend_data["release_time"]
                    
                    # Create graph using pre-generated data
                    fig, ax = plt.subplots(figsize=(8, 5))
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Different colors for each formulation
                    
                    # Get color index based on formulation number
                    formulation_index = formulation_options.index(selected_formulation)
                    color = colors[formulation_index % len(colors)]
                    
                    ax.plot(x_values, y_values, marker="o", linewidth=3, markersize=6, color=color)
                    ax.fill_between(x_values, y_values, alpha=0.3, color=color)
                    
                    # Set axis limits and labels
                    ax.set_xlim(0, release_time_value)
                    ax.set_ylim(0, 1)
                    ax.set_xlabel("Time (Days)", fontsize=12)
                    ax.set_ylabel("Performance", fontsize=12)
                    ax.set_title(f"Performance Trend - {selected_formulation}", fontsize=14, fontweight='bold')
                    
                    # Add grid for better readability
                    ax.grid(True, alpha=0.3)
                    ax.set_axisbelow(True)
                    
                    # Add performance milestones
                    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Target Threshold')
                    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.7, label='Optimal Performance')
                    ax.legend()
                    
                    st.pyplot(fig)
                else:
                    st.error(f"No performance trend data found for {selected_formulation}")
        else:
            st.warning("No performance trend data found. Please re-run optimization to generate performance trends.")

    # ── Evaluation Tab ───────────────────────────────────────────────────────
    with tab_evaluation:
        st.subheader("Evaluation Criteria")
        st.info(f"📁 Showing fixed evaluation for job: **{current_job_name}**")
        
        # Clear results button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(" ")  # Spacer
        with col2:
            if st.button("🗑️ Clear Results", key="clear_eval_results", help="Remove results from current job"):
                current_job.result_dataset = None
                st.success(f"Results cleared from job '{current_job_name}'")
                st.rerun()
        
        result_data_eval = current_job.result_dataset

        # First row: two columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Job Information**")
            st.write(f"**Job:** {current_job_name}")
            st.write(f"**Type:** {result_data_eval.get('type', 'Unknown')}")
            st.write(f"**Model:** {result_data_eval.get('model_name', 'Unknown')}")
            st.write(f"**Completed:** {result_data_eval.get('timestamp', 'Unknown')}")
            
        with col2:
            st.markdown("**Evaluation Criteria**")
            # Use pre-generated evaluation criteria from optimization
            if 'evaluation_criteria' in result_data_eval:
                crit_comp = {k: f"{v}%" for k, v in result_data_eval['evaluation_criteria'].items()}
                df_crit = pd.DataFrame([crit_comp])
                st.table(df_crit)
            else:
                st.warning("No evaluation criteria found. Please re-run optimization.")

        # Second row: Evaluation results
        st.subheader("Evaluation Results")
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            # Use pre-generated evaluation scores from optimization
            if 'evaluation_scores' in result_data_eval:
                eval_vals = result_data_eval['evaluation_scores']
                df_eval = pd.DataFrame([eval_vals])
                st.markdown("**Evaluation Scores (1-10)**")
                st.table(df_eval)
            else:
                st.warning("No evaluation scores found. Please re-run optimization.")
            
            # Additional metrics using stored data
            st.markdown("**Additional Metrics**")
            if 'additional_metrics' in result_data_eval:
                add_metrics = result_data_eval['additional_metrics']
                additional_metrics = {
                    "Metric": list(add_metrics.keys()),
                    "Score": [str(v) for v in add_metrics.values()],
                    "Status": ["✅ Passed" for _ in add_metrics]
                }
                df_additional = pd.DataFrame(additional_metrics)
                st.dataframe(df_additional, use_container_width=True)
            else:
                st.warning("No additional metrics found. Please re-run optimization.")
            
        with ecol2:
            st.markdown("**Evaluation Radar Chart**")
            # Use pre-generated evaluation scores for radar chart
            if 'evaluation_scores' in result_data_eval:
                eval_vals = result_data_eval['evaluation_scores']
                labels = list(eval_vals.keys())
                vals = list(eval_vals.values())
                angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                vals += vals[:1]
                angles += angles[:1]
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
                ax.plot(angles, vals, marker="o", linewidth=2, color='#ff7f0e')
                ax.fill(angles, vals, alpha=0.25, color='#ff7f0e')
                ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                ax.set_ylim(0, 10)
                ax.set_title(f"Evaluation Profile: {current_job_name}", y=1.1, fontweight='bold')
                ax.grid(True)
                st.pyplot(fig)
            else:
                st.warning("No evaluation data found for radar chart. Please re-run optimization.")
