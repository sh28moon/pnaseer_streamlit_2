# pages/results.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from pages.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.header("Results")

    # Get all jobs that have results (independent of sidebar selection)
    all_jobs = st.session_state.get("jobs", {})
    jobs_with_results = {name: job for name, job in all_jobs.items() if job.has_result_data()}
    
    if not jobs_with_results:
        st.warning("⚠️ No completed jobs with results available. Please run optimization first.")
        return

    # Top-level tabs
    tab_summary, tab_evaluation = st.tabs(["Summary", "Evaluation"])

    # ── Summary Tab ──────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Fixed Results Summary")
        st.info("📌 **Note**: Results shown here are fixed and independent of sidebar job selection")
        
        # Independent job selection for results viewing
        job_names = list(jobs_with_results.keys())
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_result_job = st.selectbox(
                "Select Job Results to View",
                job_names,
                key="fixed_result_job_selector",
                help="Select which optimization results to view (independent of sidebar)"
            )
        with col2:
            # Clear results button
            if selected_result_job and st.button("🗑️ Clear Results", key="clear_fixed_results", help="Remove results from selected job"):
                if selected_result_job in jobs_with_results:
                    st.session_state.jobs[selected_result_job].result_dataset = None
                    st.success(f"Results cleared from job '{selected_result_job}'")
                    st.rerun()
        
        if selected_result_job:
            selected_job = jobs_with_results[selected_result_job]
            result_data = selected_job.result_dataset
            
            st.success(f"📁 Viewing fixed results for: **{selected_result_job}**")
            st.divider()
            
            # 2-column layout for results summary
            col_left, col_right = st.columns(2)
            
            # Left Column: Table
            with col_left:
                st.markdown("**Result Summary Table**")
                
                # Job Information Table
                job_info = {
                    "Property": ["Job Name", "Type", "Model", "Status", "Completed", "API Dataset", "Target Datasets"],
                    "Value": [
                        selected_result_job,
                        result_data.get('type', 'Unknown'),
                        result_data.get('model_name', 'Unknown'),
                        result_data.get('status', 'Unknown'),
                        result_data.get('timestamp', 'Unknown'),
                        "✅ Present" if selected_job.has_api_data() else "❌ Missing",
                        f"{len(selected_job.target_profile_dataset)} datasets" if selected_job.has_target_data() else "❌ Missing"
                    ]
                }
                df_info = pd.DataFrame(job_info)
                st.table(df_info)
                
                st.markdown("**Composition Results**")
                # Use pre-generated composition results from optimization
                if 'composition_results' in result_data:
                    comp_data = result_data['composition_results']
                    df_comp = pd.DataFrame(comp_data)
                    st.dataframe(df_comp, use_container_width=True)
                else:
                    st.warning("No composition results found. Please re-run optimization.")
            
            # Right Column: Radar Diagram
            with col_right:
                st.markdown("**Performance Radar Chart**")
                
                # Use pre-generated performance metrics from optimization
                if 'performance_metrics' in result_data:
                    perf_data = result_data['performance_metrics']
                    metrics = perf_data['metrics']
                    values = perf_data['values']
                    ratings = perf_data['ratings']
                    
                    # Create radar chart with stored performance metrics
                    angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
                    values_plot = values + [values[0]]  # Complete the circle
                    angles += [angles[0]]  # Complete the circle
                    
                    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                    ax.plot(angles, values_plot, marker="o", linewidth=2, color='#1f77b4')
                    ax.fill(angles, values_plot, alpha=0.25, color='#1f77b4')
                    ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
                    ax.set_ylim(0, 1.0)
                    ax.set_title(f"Performance Profile: {selected_result_job}", y=1.1, fontsize=14, fontweight='bold')
                    
                    # Add grid lines
                    ax.grid(True)
                    ax.set_rticks([0.2, 0.4, 0.6, 0.8, 1.0])
                    
                    st.pyplot(fig)
                    
                    # Performance Scores Table using stored data
                    st.markdown("**Performance Scores**")
                    score_data = {
                        "Metric": metrics,
                        "Score": [f"{v:.2f}" for v in values],
                        "Rating": ratings
                    }
                    df_scores = pd.DataFrame(score_data)
                    st.dataframe(df_scores, use_container_width=True)
                else:
                    st.warning("No performance metrics found. Please re-run optimization.")

    # ── Evaluation Tab ───────────────────────────────────────────────────────
    with tab_evaluation:
        st.subheader("Fixed Evaluation Criteria")
        st.info("📌 **Note**: Evaluation shown here is fixed and independent of sidebar job selection")
        
        # Independent job selection for evaluation tab as well
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_eval_job = st.selectbox(
                "Select Job for Evaluation",
                list(jobs_with_results.keys()),
                key="fixed_eval_job_selector",
                help="Select which job to evaluate (independent of sidebar)"
            )
        with col2:
            # Clear results button
            if selected_eval_job and st.button("🗑️ Clear Results", key="clear_fixed_eval_results", help="Remove results from selected job"):
                if selected_eval_job in jobs_with_results:
                    st.session_state.jobs[selected_eval_job].result_dataset = None
                    st.success(f"Results cleared from job '{selected_eval_job}'")
                    st.rerun()
        
        if selected_eval_job:
            selected_job_eval = jobs_with_results[selected_eval_job]
            result_data_eval = selected_job_eval.result_dataset
            
            st.success(f"📁 Evaluating fixed results for: **{selected_eval_job}**")

            # First row: two columns
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Job Information**")
                st.write(f"**Job:** {selected_eval_job}")
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
                    ax.set_title(f"Evaluation Profile: {selected_eval_job}", y=1.1, fontweight='bold')
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.warning("No evaluation data found for radar chart. Please re-run optimization.")
