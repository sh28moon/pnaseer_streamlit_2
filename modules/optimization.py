# modules/optimization.py
import streamlit as st
import pandas as pd
import time
import random

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
            # Input Data Management
            st.markdown('<p class="font-medium"><b>Input Data Selection</b></p>', unsafe_allow_html=True)
            
            # Initialize selection variables
            selected_api_data = None
            selected_api_index = None
            selected_api_name = None
            selected_target_data = None
            selected_target_name = None
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**API Data**")
                if current_job.has_api_data():
                    st.success("✅ API data loaded from job")
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
                            st.info(f"Selected: {selected_api_name}")
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
                            # st.info(f"Selected: {selected_api_row}")
                    else:
                        # Single row or simple data
                        selected_api_data = api_data
                        selected_api_index = 0
                        selected_api_name = api_data['Name'].iloc[0] if 'Name' in api_data.columns else "Row 1"
                        # st.info(f"Using: {selected_api_name}")
                else:
                    st.error("❌ No API data in current job")
                    st.info("Please add API data in Input Conditions")
                    selected_api_name = None
            
            with col2:
                st.markdown("**Target Profile Data**")
                if current_job.has_target_data():
                    st.success("✅ Target data loaded from job")
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
                        # st.info(f"Selected: {selected_target_name}")                        

                else:
                    st.error("❌ No target data in current job")
                    st.info("Please add target data in Input Conditions")
                    selected_target_name = None
            
            st.divider()
 
            # Import model CSV
            st.subheader("Model Selection")
            uploaded = st.file_uploader(
                "Import a Model (CSV only)",
                type=["csv"],
                key=f"{prefix}_import"
            )
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    
                    # Validate that CSV has Name column
                    if 'Name' not in df.columns:
                        st.error("❌ Model CSV must have a 'Name' column for model identification.")
                        st.error("Expected structure: [Name, Parameter1, Parameter2, ...]")
                    elif len(df) == 0:
                        st.error("❌ Model CSV file is empty.")
                    else:
                        # Create separate model datasets for each row
                        model_datasets = {}
                        for index, row in df.iterrows():
                            model_name = str(row['Name']).strip()
                            if model_name:  # Only add if name is not empty
                                # Create single-row dataframe for this model
                                model_df = pd.DataFrame([row])
                                model_datasets[model_name] = model_df
                        
                        # Save all model datasets to job
                        if model_datasets:
                            if current_job.has_model_data():
                                current_job.model_dataset.update(model_datasets)
                            else:
                                current_job.model_dataset = model_datasets
                            
                            st.session_state.jobs[current_job_name] = current_job
                            st.success(f"✅ {len(model_datasets)} models imported from '{uploaded.name}'")
                            st.info(f"📊 Models: {', '.join(list(model_datasets.keys())[:3])}" + 
                                   (f" and {len(model_datasets)-3} more" if len(model_datasets) > 3 else ""))
                        else:
                            st.error("❌ No valid models found. Check that Name column contains values.")
                        
                except Exception as e:
                    st.error(f"❌ Error reading model file: {str(e)}")
                    st.error("Please ensure the file is a valid CSV format.")

            # Show current model in job
            if current_job.has_model_data():
                model_data = current_job.model_dataset
                model_names = list(model_data.keys())           
                
                selected = st.selectbox(
                    "Select Model for Optimization",
                    model_names,
                    key=f"{prefix}_select"
                )
                
                # if selected:
                #     st.info(f"Selected model: {selected}")
                
                # Clear model data button
                if st.button(f"🗑️ Clear All Model Data", key=f"clear_model_{prefix}", help="Remove all model data from current job"):
                    current_job.model_dataset = None
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"All model data cleared from job '{current_job_name}'")
                    st.rerun()
            else:
                st.info("No models in current job yet.")
                selected = None

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
                    
                    # Generate composition results
                    composition_results = {
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
                        "additional_metrics": additional_metrics
                    }
                    
                    current_job.result_dataset = result_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Results with datasets generated and saved to job '{current_job_name}' using:")
                    st.info(f"• API: {selected_api_name}")
                    st.info(f"• Target: {selected_target_name}")
                    st.info(f"• Model: {selected}")
                    st.info("• All result datasets generated and stored")

    # Render each tab
    render_model_tab("model#1", tab_encap)

