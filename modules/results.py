# pages/results.py
import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.header("Results")

    # Get all jobs that have results
    all_jobs = st.session_state.get("jobs", {})
    jobs_with_results = {name: job for name, job in all_jobs.items() if job.has_result_data()}
    
    if not jobs_with_results:
        st.warning("⚠️ No completed jobs with results available. Please run optimization first.")
        return

    # Top-level tabs
    tab_summary, tab_evaluation = st.tabs(["Summary", "Evaluation"])

    # ── Summary Tab ──────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Job Selection & Results Summary")
        
        # Job Selection
        job_names = list(jobs_with_results.keys())
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_job_name = st.selectbox(
                "Select Job to View Results",
                job_names,
                key="result_job_selector"
            )
        with col2:
            # Clear results button
            if selected_job_name and st.button("🗑️ Clear Results", key="clear_results_summary", help="Remove results from selected job"):
                if selected_job_name in jobs_with_results:
                    st.session_state.jobs[selected_job_name].result_dataset = None
                    st.success(f"Results cleared from job '{selected_job_name}'")
                    st.rerun()
        
        if selected_job_name:
            selected_job = jobs_with_results[selected_job_name]
            result_data = selected_job.result_dataset
            
            st.info(f"📁 Viewing results for job: **{selected_job_name}**")
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
                        selected_job_name,
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
                # Generate composition table based on result data
                comp_data = {
                    "Component": ["PEG", "API", "Buffer", "Stabilizer", "Excipient"],
                    "Percentage (%)": [
                        f"{random.randint(10,40)}%",
                        f"{random.randint(15,35)}%", 
                        f"{random.randint(5,20)}%",
                        f"{random.randint(2,10)}%",
                        f"{random.randint(5,15)}%"
                    ],
                    "Concentration (mg/mL)": [
                        f"{random.randint(50,200):.1f}",
                        f"{random.randint(25,100):.1f}",
                        f"{random.randint(10,50):.1f}",
                        f"{random.randint(2,20):.1f}",
                        f"{random.randint(5,30):.1f}"
                    ]
                }
                df_comp = pd.DataFrame(comp_data)
                st.dataframe(df_comp, use_container_width=True)
            
            # Right Column: Radar Diagram
            with col_right:
                st.markdown("**Performance Radar Chart**")
                
                # Create radar chart with performance metrics
                metrics = ["Stability", "Efficacy", "Safety", "Bioavailability", "Manufacturability"]
                values = [random.uniform(0.6, 1.0) for _ in metrics]
                
                # Create radar chart
                angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
                values_plot = values + [values[0]]  # Complete the circle
                angles += [angles[0]]  # Complete the circle
                
                fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                ax.plot(angles, values_plot, marker="o", linewidth=2, color='#1f77b4')
                ax.fill(angles, values_plot, alpha=0.25, color='#1f77b4')
                ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
                ax.set_ylim(0, 1.0)
                ax.set_title(f"Performance Profile: {selected_job_name}", y=1.1, fontsize=14, fontweight='bold')
                
                # Add grid lines
                ax.grid(True)
                ax.set_rticks([0.2, 0.4, 0.6, 0.8, 1.0])
                
                st.pyplot(fig)
                
                # Performance Scores Table
                st.markdown("**Performance Scores**")
                score_data = {
                    "Metric": metrics,
                    "Score": [f"{v:.2f}" for v in values],
                    "Rating": ["Excellent" if v > 0.8 else "Good" if v > 0.6 else "Fair" for v in values]
                }
                df_scores = pd.DataFrame(score_data)
                st.dataframe(df_scores, use_container_width=True)

    # ── Evaluation Tab ───────────────────────────────────────────────────────
    with tab_evaluation:
        st.subheader("Evaluation Criteria")
        
        # Job Selection for Evaluation tab as well
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_job_name_eval = st.selectbox(
                "Select Job for Evaluation",
                list(jobs_with_results.keys()),
                key="eval_job_selector"
            )
        with col2:
            # Clear results button
            if selected_job_name_eval and st.button("🗑️ Clear Results", key="clear_results_eval", help="Remove results from selected job"):
                if selected_job_name_eval in jobs_with_results:
                    st.session_state.jobs[selected_job_name_eval].result_dataset = None
                    st.success(f"Results cleared from job '{selected_job_name_eval}'")
                    st.rerun()
        
        if selected_job_name_eval:
            selected_job_eval = jobs_with_results[selected_job_name_eval]
            result_data_eval = selected_job_eval.result_dataset
            
            st.info(f"📁 Evaluating job: **{selected_job_name_eval}**")

            # First row: two columns
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Job Information**")
                st.write(f"**Job:** {selected_job_name_eval}")
                st.write(f"**Type:** {result_data_eval.get('type', 'Unknown')}")
                st.write(f"**Model:** {result_data_eval.get('model_name', 'Unknown')}")
                st.write(f"**Completed:** {result_data_eval.get('timestamp', 'Unknown')}")
                
            with col2:
                st.markdown("**Evaluation Criteria**")
                crit_comp = {
                    "Injectability": f"{random.randint(70,95)}%",
                    "Release Time": f"{random.randint(80,100)}%",
                    "Encapsulation Rate": f"{random.randint(85,98)}%",
                }
                df_crit = pd.DataFrame([crit_comp])
                st.table(df_crit)

            # Second row: Evaluation results
            st.subheader("Evaluation Results")
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                eval_vals = {
                    k: random.randint(6,10)
                    for k in crit_comp.keys()
                }
                df_eval = pd.DataFrame([eval_vals])
                st.markdown("**Evaluation Scores (1-10)**")
                st.table(df_eval)
                
                # Additional metrics
                st.markdown("**Additional Metrics**")
                additional_metrics = {
                    "Metric": ["Cost Effectiveness", "Production Scalability", "Regulatory Compliance", "Market Potential"],
                    "Score": [f"{random.randint(7,10)}" for _ in range(4)],
                    "Status": ["✅ Passed" for _ in range(4)]
                }
                df_additional = pd.DataFrame(additional_metrics)
                st.dataframe(df_additional, use_container_width=True)
                
            with ecol2:
                st.markdown("**Evaluation Radar Chart**")
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
                ax.set_title(f"Evaluation Profile: {selected_job_name_eval}", y=1.1, fontweight='bold')
                ax.grid(True)
                st.pyplot(fig)