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
        
        # 3rd Row: Performance Trend Analysis with Radar Comparison
        st.markdown("**Performance Trend Analysis**")
        
        # Use pre-generated performance trend data from optimization
        if 'performance_trends' in result_data:
            performance_trends = result_data['performance_trends']
            
            # Formulation selector (full width)
            formulation_options = list(performance_trends.keys())
            selected_formulation = st.selectbox(
                "Select Formulation to Analyze:",
                formulation_options,
                key="formulation_selector"
            )
            
            # Show composition data for selected formulation in expander
            if 'composition_results' in result_data:
                comp_data_list = result_data['composition_results']
                # Find the composition data for selected formulation
                selected_comp = None
                for comp in comp_data_list:
                    if comp.get("Row") == selected_formulation:
                        selected_comp = comp
                        break
                
                if selected_comp:
                    with st.expander(f"📋 {selected_formulation} Composition Details", expanded=False):
                        for key, value in selected_comp.items():
                            if key != "Row":  # Skip the row identifier
                                st.write(f"• **{key}**: {value}")
            
            # Two column layout for radar and performance trend
            col_radar, col_performance = st.columns(2)
            
            with col_radar:
                st.markdown(f"**Target vs Result Comparison - {selected_formulation}**")
                
                # Get target profile data
                if 'selected_target_data' in result_data:
                    target_data = result_data['selected_target_data']
                    
                    if len(target_data.columns) >= 4:  # Ensure we have the required columns
                        # Extract target values (columns 1, 2, 3 after Name column)
                        target_modulus = float(str(target_data.iloc[0, 1]).replace('%', '').replace('Day', '').strip())
                        target_encap_rate = float(str(target_data.iloc[0, 2]).replace('%', '').replace('Day', '').strip())
                        target_release_time = float(str(target_data.iloc[0, 3]).replace('%', '').replace('Day', '').strip())
                        
                        # Generate result values based on formulation (simulate optimization results)
                        import random
                        formulation_index = formulation_options.index(selected_formulation)
                        
                        # Set seed for consistent results per formulation
                        random.seed(hash(f"{current_job_name}_{selected_formulation}_radar") % 2147483647)
                        
                        # Generate result values with some variance from target (±10-20%)
                        result_modulus = target_modulus * random.uniform(0.85, 1.15)
                        result_encap_rate = target_encap_rate * random.uniform(0.9, 1.1)
                        result_release_time = target_release_time * random.uniform(0.8, 1.2)
                        
                        # Normalize values for radar chart (scale to 0-100 for better visualization)
                        max_modulus = max(target_modulus, result_modulus) * 1.2
                        max_encap_rate = max(target_encap_rate, result_encap_rate) * 1.2
                        max_release_time = max(target_release_time, result_release_time) * 1.2
                        
                        # Normalized values for radar chart
                        target_norm = [
                            (target_modulus / max_modulus) * 100,
                            (target_encap_rate / max_encap_rate) * 100,
                            (target_release_time / max_release_time) * 100
                        ]
                        
                        result_norm = [
                            (result_modulus / max_modulus) * 100,
                            (result_encap_rate / max_encap_rate) * 100,
                            (result_release_time / max_release_time) * 100
                        ]
                        
                        # Create radar chart
                        labels = ['Modulus', 'Encapsulation Rate', 'Release Time (Day)']
                        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                        
                        # Close the radar chart
                        target_norm += target_norm[:1]
                        result_norm += result_norm[:1]
                        angles += angles[:1]
                        
                        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
                        
                        # Plot target profile line
                        ax.plot(angles, target_norm, marker="o", linewidth=2, markersize=6, 
                               color='blue', label='Target Profile', alpha=0.8)
                        ax.fill(angles, target_norm, alpha=0.15, color='blue')
                        
                        # Plot result line
                        ax.plot(angles, result_norm, marker="s", linewidth=2, markersize=6, 
                               color='red', label=f'{selected_formulation} Result', alpha=0.8)
                        ax.fill(angles, result_norm, alpha=0.15, color='red')
                        
                        # Customize radar chart
                        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                        ax.set_ylim(0, 100)
                        ax.set_title(f"Target vs Result Comparison\n{selected_formulation}", 
                                   y=1.08, fontsize=12, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
                        
                        # Add value labels
                        for angle, target_val, result_val, label in zip(angles[:-1], target_norm[:-1], result_norm[:-1], labels):
                            # Target values
                            ax.text(angle, target_val + 5, f'T:{target_val:.1f}', 
                                   ha='center', va='center', fontsize=8, color='blue', fontweight='bold')
                            # Result values  
                            ax.text(angle, result_val - 8, f'R:{result_val:.1f}', 
                                   ha='center', va='center', fontsize=8, color='red', fontweight='bold')
                        
                        st.pyplot(fig)
                        
                        # Show actual values below chart
                        st.markdown("**Actual Values:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Target:**")
                            st.write(f"• Modulus: {target_modulus:.2f}")
                            st.write(f"• Encap Rate: {target_encap_rate:.2f}")
                            st.write(f"• Release Time: {target_release_time:.2f}")
                        with col2:
                            st.markdown("**Result:**")
                            st.write(f"• Modulus: {result_modulus:.2f}")
                            st.write(f"• Encap Rate: {result_encap_rate:.2f}")
                            st.write(f"• Release Time: {result_release_time:.2f}")
                    else:
                        st.warning("Insufficient target data columns for radar comparison")
                else:
                    st.warning("No target data found for comparison")
            
            with col_performance:
                st.markdown(f"**Performance Trend - {selected_formulation}**")
                
                # Get pre-generated performance trend data for selected formulation
                if selected_formulation in performance_trends:
                    trend_data = performance_trends[selected_formulation]
                    x_values = trend_data["x_values"]
                    y_values = trend_data["y_values"]
                    release_time_value = trend_data["release_time"]
                    
                    # Create graph using pre-generated data
                    fig, ax = plt.subplots(figsize=(6, 5))
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
                    ax.set_title(f"Performance Over Time", fontsize=12, fontweight='bold')
                    
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
        st.subheader("Evaluation")
        st.info(f"📁 Working on job: **{current_job_name}**")
        
        # Initialize evaluation data storage in job if not exists
        if not hasattr(current_job, 'evaluation_criteria_data'):
            current_job.evaluation_criteria_data = None
        if not hasattr(current_job, 'evaluation_results_data'):
            current_job.evaluation_results_data = None
        
        # 1st Row: Evaluation Criteria Import, Clear, and Start Evaluation
        st.markdown("**Evaluation Setup**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Import Evaluation Criteria**")
            uploaded_criteria = st.file_uploader(
                "Upload Evaluation Criteria (CSV)",
                type=["csv"],
                key="evaluation_criteria_file",
                help="CSV file with evaluation criteria as column headers"
            )
            
            if uploaded_criteria:
                try:
                    df_criteria = pd.read_csv(uploaded_criteria)
                    if len(df_criteria.columns) > 0:
                        current_job.evaluation_criteria_data = df_criteria
                        st.session_state.jobs[current_job_name] = current_job
                        st.success(f"✅ {len(df_criteria.columns)} criteria loaded")
                        
                        # Show preview of criteria
                        with st.expander("📋 Criteria Preview", expanded=False):
                            st.write("**Evaluation Criteria:**")
                            for col in df_criteria.columns:
                                st.write(f"• {col}")
                    else:
                        st.error("❌ Empty file or no columns found")
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        with col2:
            st.markdown("**Clear Criteria**")
            if current_job.evaluation_criteria_data is not None:
                if st.button("🗑️ Clear Criteria", key="clear_criteria", help="Clear imported evaluation criteria"):
                    current_job.evaluation_criteria_data = None
                    current_job.evaluation_results_data = None  # Also clear results
                    st.session_state.jobs[current_job_name] = current_job
                    st.success("Evaluation criteria cleared")
                    st.rerun()
                    
                # Show current criteria status
                criteria_count = len(current_job.evaluation_criteria_data.columns)
                st.info(f"📊 {criteria_count} criteria loaded")
            else:
                st.button("🗑️ Clear Criteria", key="clear_criteria_disabled", disabled=True)
                st.info("No criteria imported")
        
        with col3:
            st.markdown("**Start Evaluation**")
            can_evaluate = (current_job.evaluation_criteria_data is not None and 
                          current_job.has_result_data())
            
            if st.button("🚀 Start Evaluation", key="start_evaluation", disabled=not can_evaluate):
                if can_evaluate:
                    # Generate evaluation scores based on imported criteria
                    criteria_columns = current_job.evaluation_criteria_data.columns.tolist()
                    
                    # Generate random scores (1-10) for each criterion
                    import random
                    evaluation_scores = {}
                    for criterion in criteria_columns:
                        evaluation_scores[criterion] = random.randint(1, 10)
                    
                    # Store evaluation results in job
                    current_job.evaluation_results_data = {
                        "scores": evaluation_scores,
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.jobs[current_job_name] = current_job
                    
                    st.success("✅ Evaluation completed!")
                    st.rerun()
                else:
                    if not current_job.has_result_data():
                        st.error("❌ No optimization results found. Please run optimization first.")
                    else:
                        st.error("❌ No evaluation criteria imported. Please import criteria first.")
            
            # Show evaluation status
            if not can_evaluate:
                missing = []
                if not current_job.has_result_data():
                    missing.append("optimization results")
                if current_job.evaluation_criteria_data is None:
                    missing.append("evaluation criteria")
                st.warning(f"Missing: {', '.join(missing)}")
            else:
                st.success("✅ Ready to evaluate")
        
        st.divider()
        
        # 2nd Row: Evaluation Results
        st.markdown("**Evaluation Results**")
        
        if current_job.evaluation_results_data is not None:
            evaluation_scores = current_job.evaluation_results_data["scores"]
            eval_timestamp = current_job.evaluation_results_data["timestamp"]
            
            # Top: Evaluation Scores Table
            st.markdown(f"**Evaluation Scores (1-10)** - *Completed: {eval_timestamp}*")
            df_eval_scores = pd.DataFrame([evaluation_scores])
            st.table(df_eval_scores)
            
            st.divider()
            
            # Bottom: Radar Chart
            st.markdown("**Evaluation Radar Chart**")
            
            labels = list(evaluation_scores.keys())
            vals = list(evaluation_scores.values())
            
            if len(labels) > 0:
                # Create radar chart
                angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                vals_plot = vals + vals[:1]  # Complete the circle
                angles_plot = angles + angles[:1]  # Complete the circle
                
                fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
                ax.plot(angles_plot, vals_plot, marker="o", linewidth=3, markersize=8, color='#ff7f0e')
                ax.fill(angles_plot, vals_plot, alpha=0.25, color='#ff7f0e')
                ax.set_thetagrids(np.degrees(angles), labels)
                ax.set_ylim(0, 10)
                ax.set_title(f"Evaluation Profile: {current_job_name}", y=1.08, fontsize=16, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Add score labels on the chart
                for angle, val, label in zip(angles, vals, labels):
                    ax.text(angle, val + 0.5, str(val), ha='center', va='center', 
                           fontsize=10, fontweight='bold', color='red')
                
                st.pyplot(fig)
            else:
                st.warning("No evaluation scores to display in radar chart")
                
        else:
            # Show blank state before evaluation
            st.info("🔍 **No evaluation results yet.**")
            st.markdown("**Instructions:**")
            st.markdown("1. Import evaluation criteria (CSV file)")
            st.markdown("2. Ensure optimization has been completed")
            st.markdown("3. Click 'Start Evaluation' to generate scores")
            st.markdown("4. Results will appear here with scores and radar chart")
