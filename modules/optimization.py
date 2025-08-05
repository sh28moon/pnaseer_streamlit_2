# pages/optimization.py
import streamlit as st
import pandas as pd
import time

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
    tab_encap, tab_form = st.tabs(["Encapsulation", "Formulation"])

    def render_model_tab(prefix, tab):
        with tab:
            st.markdown('<p class="font-medium"><b>Model Selection</b></p>', unsafe_allow_html=True)
            
            # Show Input Data Status
            st.subheader("Input Data Status")
            
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
                            st.info(f"Selected: {selected_api_row}")
                    else:
                        # Single row or simple data
                        selected_api_data = api_data
                        selected_api_index = 0
                        selected_api_name = api_data['Name'].iloc[0] if 'Name' in api_data.columns else "Row 1"
                        st.info(f"Using: {selected_api_name}")
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
                        st.info(f"Selected: {selected_target_name}")
                        
                    st.write(f"📊 Available: {len(target_data)} dataset(s)")
                    for i, name in enumerate(target_names[:2]):
                        symbol = "👉" if name == selected_target_name else "•"
                        st.write(f"{symbol} {name}")
                    if len(target_names) > 2:
                        st.write(f"• ... and {len(target_names) - 2} more")
                else:
                    st.error("❌ No target data in current job")
                    st.info("Please add target data in Input Conditions")
            
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
                st.subheader("Available Models in Job")
                model_data = current_job.model_dataset
                model_names = list(model_data.keys())
                
                st.write(f"**{len(model_names)} model(s) available:**")
                for name in model_names[:5]:  # Show first 5 model names
                    st.write(f"• {name}")
                if len(model_names) > 5:
                    st.write(f"• ... and {len(model_names) - 5} more")
                
                selected = st.selectbox(
                    "Select Model for Optimization",
                    model_names,
                    key=f"{prefix}_select"
                )
                
                if selected:
                    st.info(f"Selected model: {selected}")
                
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
            st.subheader("Calculate")
            
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
            
            # Summary table of selections
            st.markdown("**Optimization Summary - Selected Data**")
            
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

                    # Create result and save to job with selected data
                    import datetime
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
                        "status": "completed"
                    }
                    
                    current_job.result_dataset = result_data
                    st.session_state.jobs[current_job_name] = current_job
                    st.success(f"Results saved to job '{current_job_name}' using:")
                    st.info(f"• API: {selected_api_name}")
                    st.info(f"• Target: {selected_target_name}")
                    st.info(f"• Model: {selected}")

    # Render each tab
    render_model_tab("encapsulation", tab_encap)
    render_model_tab("formulation", tab_form)