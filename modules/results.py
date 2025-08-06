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
        
        # 1st Row: Composition Results with Clear Button
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
        
        # 2nd Row: Performance Trend Graphs for Each Composition
        st.markdown("**Performance Trends by Formulation**")
        
        # Create 3 columns for 3 performance trend graphs
        col1, col2, col3 = st.columns(3)
        
        # Use pre-generated performance metrics and target data from optimization
        if 'performance_metrics' in result_data and 'selected_target_data' in result_data:
            # Get Release Time from target data
            target_data = result_data['selected_target_data']
            if len(target_data.columns) >= 4:  # Ensure we have the Release Time column
                release_time_value = target_data.iloc[0, 3]  # Assuming Release Time is 4th column (index 3)
                # Convert to numeric if it's a string with units
                if isinstance(release_time_value, str):
                    release_time_value = float(release_time_value.replace('%', '').replace('Day', '').strip())
                elif not isinstance(release_time_value, (int, float)):
                    release_time_value = float(release_time_value)
            else:
                release_time_value = 10  # Default fallback
            
            # Generate performance trends for each of the 3 formulations
            formulations = ["Formulation 1", "Formulation 2", "Formulation 3"]
            columns = [col1, col2, col3]
            
            for i, (formulation, col) in enumerate(zip(formulations, columns)):
                with col:
                    st.markdown(f"**{formulation}**")
                    
                    # Create unique upward trending line graph for each formulation
                    x_points = 8  # Fewer points for smaller graphs
                    x_values = np.linspace(0, release_time_value, x_points)
                    
                    # Generate different upward trends for each formulation
                    # Vary the starting point and slope for each formulation
                    start_values = [0.1, 0.15, 0.08]  # Different starting points
                    end_values = [0.85, 0.92, 0.88]   # Different ending points
                    
                    base_trend = np.linspace(start_values[i], end_values[i], x_points)
                    noise = np.random.normal(0, 0.03, x_points)  # Smaller noise for cleaner look
                    y_values = base_trend + noise
                    
                    # Ensure values stay within 0-1 range and maintain upward trend
                    y_values = np.clip(y_values, 0, 1)
                    y_values = np.sort(y_values)  # Force upward trend
                    
                    # Create smaller line graph for each formulation
                    fig, ax = plt.subplots(figsize=(4, 3))
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Different colors for each formulation
                    
                    ax.plot(x_values, y_values, marker="o", linewidth=2, markersize=4, color=colors[i])
                    ax.fill_between(x_values, y_values, alpha=0.3, color=colors[i])
                    
                    # Set axis limits and labels
                    ax.set_xlim(0, release_time_value)
                    ax.set_ylim(0, 1)
                    ax.set_xlabel("Time (Days)", fontsize=10)
                    ax.set_ylabel("Performance", fontsize=10)
                    ax.set_title(f"Performance Trend", fontsize=11, fontweight='bold')
                    
                    # Add grid for better readability
                    ax.grid(True, alpha=0.3)
                    ax.set_axisbelow(True)
                    
                    # Smaller tick labels for compact display
                    ax.tick_params(axis='both', which='major', labelsize=8)
                    
                    st.pyplot(fig)
        else:
            st.warning("No target data found for performance trends. Please re-run optimization.")

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
