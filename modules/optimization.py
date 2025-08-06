# modules/optimization.py
import streamlit as st
import pandas as pd
import time
import random
import numpy as np

from modules.global_css import GLOBAL_CSS
st.markdown(f"<style>{GLOBAL_CSS}</style>", unsafe_allow_html=True)

def show():
    st.header("Optimization")

    # Check if a job is selected
    current_job_name = st.session_state.get("current_job")
    if not current_job_name or current_job_name not in st.session_state.get("jobs", {}):
        st.warning("⚠️ No job selected. Please create and select a job from the sidebar to continue.")
        return
    
    current_job = st.session_state.jobs[current_job_name]
    st.info(f"📁 Working on job: **{current_job_name}**")

    # Top-level tabs
    tab_encap = st.tabs(["Model #1"])[0]

    def render_model_tab(prefix, tab):
        with tab:
            # All selections in one row with three columns
            st.markdown('<p class="font-medium"><b>Input Data Selection & Model Selection</b></p>', unsafe_allow_html=True)
            
            # Initialize selection variables
            selected_api_data = None
            selected_api_index = None
            selected_api_name = None
            selected_target_data = None
            selected_target_name = None
            
            # Three-column layout: Input Data Selection (2 cols) + Model Selection (1 col)
            col1, col2, col3 = st.columns(3)
            
            # Column 1: API Data (Input Data Selection - Part 1)
            with col1:
                st.markdown("**API Data**")
                if current_job.has_api_data():
                    api_data = current_job.api_dataset
                    
                    # API Data Selection
                    if hasattr(api_data, 'shape') and len(api_data) > 1:
                        # Multiple rows available for selection - use Name column values
                        if 'Name' in api_data.columns:
                            api_name_options = api_data['Name'].tolist()
                            selected_api_name = st.selectbox(
                                "Select API Data",
                                api_name_options,
                                key=f"{prefix}_api_select"
                            )
                            selected_api_index = api_name_options.index(selected_api_name)
                            selected_api_data = api_data.iloc[[selected_api_index]]
                        else:
                            # Fallback to row numbers if no Name column
                            api_row_options = [f"Row {i+1}" for i in range(len(api_data))]
                            selected_api_row = st.selectbox(
                                "Select API Data Row",
                                api_row_options,
                                key=f"{prefix}_api_select"
                            )
                            selected_api_index = api_row_options.index(selected_api_row)
                            selected_api_data = api_data.iloc[[selected_api_index]]
                            selected_api_name = f"Row {selected_api_index + 1}"
                    else:
                        # Single row or simple data
                        selected_api_data = api_data
                        selected_api_index = 0
                        selected_api_name = api_data['Name'].iloc[0] if 'Name' in api_data.columns else "Row 1"
                else:
                    st.error("❌ No API data in current job")
                    selected_api_name = None
            
            # Column 2: Target Profile Data (Input Data Selection - Part 2)
            with col2:
                st.markdown("**Target Profile Data**")
                if current_job.has_target_data():
                    target_data = current_job.target_profile_dataset
                    
                    # Target Profile Data Selection
                    target_names = list(target_data.keys())
                    selected_target_name = st.selectbox(
                        "Select Target Dataset",
                        target_names,
                        key=f"{prefix}_target_select"
                    )
                    
                    if selected_target_name:
                        selected_target_data = target_data[selected_target_name]
                else:
                    st.error("❌ No target data in current job")
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
            
            # Check if all required data is available
            has_api_data = current_job.has_api_data() and selected_api_data is not None and selected_api_name is not None
            has_target_data = current_job.has_target_data() and selected_target_data is not None
            has_model_data = current_job.get_model_status() and selected
            
            # Status indicators
            col1, col2, col3 = st.columns(3)
            with col1:
                status_api = "✅" if has_api_data else "❌"
                st.write(f"{status_api} API Data Selected")
            with col2:
                status_target = "✅" if has_target_data else "❌"
                st.write(f"{status_target} Target Data Selected") 
            with col3:
                status_model = "✅" if has_model_data else "❌"
                st.write(f"{status_model} Model Selected")       
            
            # Show three separate tables with full values
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Selected API Data**")
                if has_api_data and selected_api_data is not None:
                    st.markdown(f"*{selected_api_name}*")
                    st.dataframe(selected_api_data, use_container_width=True)
                else:
                    st.warning("No API data selected")
            
            with col2:
                st.markdown("**Selected Target Profile**")
                if has_target_data and selected_target_data is not None:
                    st.markdown(f"*{selected_target_name}*")
                    st.dataframe(selected_target_data, use_container_width=True)
                else:
                    st.warning("No target data selected")
            
            with col3:
                st.markdown("**Selected Model**")
                if has_model_data and selected:
                    st.markdown(f"*{selected}*")
                    model_df = current_job.model_dataset[selected]
                    st.dataframe(model_df, use_container_width=True)
                else:
                    st.warning("No model selected")
            
            # Submit button - only enabled if all data is ready
            can_submit = has_api_data and has_target_data and has_model_data

            if st.button("Submit Job", key=f"{prefix}_run", disabled=not can_submit):
                if not can_submit:
                    st.error("Please ensure API data, target data, and model are all selected before submitting.")
                else:
                    progress = st.progress(0)
                    for i in range(101):
                        time.sleep(0.02)
                        progress.progress(i)
                    st.success("Completed Calculation")

                    # Create comprehensive result datasets during optimization
                    import datetime
                    
                    # Generate composition results - 3 rows with 4 components, all percentages sum to 100%
                    composition_results = []
                    for i in range(3):  # Create 3 rows
                        buffer_pct = random.randint(80, 95)  # Buffer between 80-95%
                        remaining_pct = 100 - buffer_pct
                        
                        # Distribute remaining percentage among other 3 components
                        assembled_pct = random.randint(1, remaining_pct - 2)
                        excipient_pct = random.randint(1, remaining_pct - assembled_pct - 1)
                        stabilizer_pct = remaining_pct - assembled_pct - excipient_pct
                        
                        composition_results.append({
                            "Row": f"Formulation {i+1}",
                            "Assembled Polymer": f"{assembled_pct}%",
                            "Excipient Polymer": f"{excipient_pct}%", 
                            "Stabilizer": f"{stabilizer_pct}%",
                            "Buffer": f"{buffer_pct}%"
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
                    
                    # Generate evaluation criteria and scores
                    evaluation_criteria = {
                        "Injectability": random.randint(70,95),
                        "Release Time": random.randint(80,100),
                        "Encapsulation Rate": random.randint(85,98)
                    }
                    
                    evaluation_scores = {
                        k: random.randint(6,10) for k in evaluation_criteria.keys()
                    }
                    
                    # Generate additional metrics
                    additional_metrics = {
                        "Cost Effectiveness": random.randint(7,10),
                        "Production Scalability": random.randint(7,10),
                        "Regulatory Compliance": random.randint(7,10),
                        "Market Potential": random.randint(7,10)
                    }
                    
                    # Generate performance trend data for all 3 formulations (NEW)
                    # Get Release Time from target data
                    if len(selected_target_data.columns) >= 4:
                        release_time_value = selected_target_data.iloc[0, 3]
                        # Convert to numeric if it's a string with units
                        if isinstance(release_time_value, str):
                            release_time_value = float(release_time_value.replace('%', '').replace('Day', '').strip())
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
                    
                    # Create comprehensive result data with all generated datasets
                    result_data = {
                        "type": prefix,
                        "model_name": selected,
                        "selected_api_data": selected_api_data,
                        "selected_api_name": selected_api_name,
                        "selected_api_row": selected_api_index if selected_api_index is not None else 0,
                        "selected_target_data": selected_target_data,
                        "selected_target_name": selected_target_name,
                        "model_data": current_job.model_dataset[selected] if selected else None,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "completed",
                        
                        # Generated result datasets
                        "composition_results": composition_results,
                        "performance_metrics": performance_metrics,
                        "evaluation_criteria": evaluation_criteria,
                        "evaluation_scores": evaluation_scores,
                        "additional_metrics": additional_metrics,
                        "performance_trends": performance_trends  # NEW: Fixed performance trend data
                    }
                    
                    current_job.result_dataset = result_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Results with datasets generated and saved to job '{current_job_name}' using:")
                    st.info(f"• API: {selected_api_name}")
                    st.info(f"• Target: {selected_target_name}")
                    st.info(f"• Model: {selected}")
                    st.info("• All result datasets generated and stored")
                    st.info("• Performance trends pre-calculated for consistent display")

    # Render each tab
    render_model_tab("model#1", tab_encap)
