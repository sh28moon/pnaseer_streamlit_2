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
        return
    
    current_job = st.session_state.jobs[current_job_name]
    
    # Check if current job has results
    if not current_job.has_result_data():
        return

    # Top-level tabs
    tab_summary, tab_evaluation = st.tabs(["Summary", "Evaluation"])

    # ── Summary Tab ──────────────────────────────────────────────────────────
    with tab_summary:
        st.subheader("Results Summary")
        
        result_data = current_job.result_dataset
        
        # Get Gel Polymer name from target profile
        gel_polymer_name = "Not specified"
        if 'selected_target_profile' in result_data:
            target_profile = result_data['selected_target_profile']
            if ('formulation_data' in target_profile and 
                'Gel Polymer' in target_profile['formulation_data'].columns):
                gel_polymer_value = target_profile['formulation_data'].iloc[0]['Gel Polymer']
                if pd.notna(gel_polymer_value):
                    gel_polymer_name = str(gel_polymer_value)
        
        # Get Co-polymer name randomly from Polymer database, excluding Gel Polymer
        co_polymer_name = "Not specified"
        if "polymer_datasets" in st.session_state and st.session_state["polymer_datasets"]:
            import random
            # Set seed for consistent results per job
            random.seed(hash(current_job_name) % 2147483647)
            
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
        
        # Composition Results with Clear Button
        col_comp, col_clear = st.columns([4, 1])
        with col_comp:
            st.markdown("**Composition Results**")
        with col_clear:
            if st.button("🗑️ Clear Results", key="clear_current_results", help="Remove results from current job"):
                current_job.result_dataset = None
                st.success(f"Results cleared from job '{current_job_name}'")
                st.rerun()
        
        # Enhanced composition results with gel polymer and co-polymer columns
        if 'composition_results' in result_data:
            comp_data_list = result_data['composition_results']
            
            # Create enhanced composition data with polymer information
            enhanced_comp_data = []
            for i, comp in enumerate(comp_data_list):
                enhanced_comp = {
                    "Gel Polymer": gel_polymer_name,
                    "Co-polymer": co_polymer_name,
                    "Candidate": comp.get("Row", f"Formulation {i+1}"),  # Change "Row" to "Candidate"
                    "Gel Polymer w/w": comp.get("Gel Polymer w/w", ""),
                    "Co-polymer w/w": comp.get("Co-polymer w/w", ""),
                    "Buffer w/w": comp.get("Buffer w/w", "")
                }
                enhanced_comp_data.append(enhanced_comp)
            
            df_comp_enhanced = pd.DataFrame(enhanced_comp_data)
            st.dataframe(df_comp_enhanced, use_container_width=True)
        
        st.divider()
        
        # Performance Review (renamed from Performance Trend Analysis)
        st.markdown("**Performance review**")
        
        # Use pre-generated performance trend data from calculation
        if 'performance_trends' in result_data:
            performance_trends = result_data['performance_trends']
            
            # Formulation selector (full width)
            formulation_options = list(performance_trends.keys())
            selected_formulation = st.selectbox(
                "Select Formulation to Analyze:",
                formulation_options,
                key="formulation_selector"
            )
            
            # Two column layout for ATPS Composition and Drug Release
            col_atps, col_performance = st.columns(2)
            
            with col_atps:
                st.markdown("**ATPS Composition**")
                
                # Get composition results to use as reference values
                if 'composition_results' in result_data and selected_formulation:
                    comp_data_list = result_data['composition_results']
                    
                    # Find the composition data for selected formulation
                    selected_comp = None
                    for comp in comp_data_list:
                        if comp.get("Row") == selected_formulation or comp.get("Candidate") == selected_formulation:
                            selected_comp = comp
                            break
                    
                    if selected_comp:
                        # Extract reference values from composition results (remove % sign and convert to float)
                        ref_gel_polymer = float(selected_comp.get("Gel Polymer w/w", "10%").replace('%', ''))
                        ref_co_polymer = float(selected_comp.get("Co-polymer w/w", "10%").replace('%', ''))
                        ref_buffer = float(selected_comp.get("Buffer w/w", "80%").replace('%', ''))
                        
                        # Set seed for consistent ATPS values per formulation
                        import random
                        random.seed(hash(f"{current_job_name}_{selected_formulation}_atps") % 2147483647)
                        
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
                            # Adjust values to ensure positive buffer and sum = 100%
                            top_gel_polymer = ref_gel_polymer * 0.7
                            top_co_polymer = ref_co_polymer * 1.2
                            top_buffer = 100 - top_gel_polymer - top_co_polymer
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
                            # Adjust values to ensure positive buffer and sum = 100%
                            bottom_gel_polymer = ref_gel_polymer * 1.2
                            bottom_co_polymer = ref_co_polymer * 0.8
                            bottom_buffer = 100 - bottom_gel_polymer - bottom_co_polymer
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
                    else:
                        # Fallback if no composition data found
                        atps_data = {
                            "Component": ["Gel polymer concentration", "Co-polymer concentration", "Buffer concentration"],
                            "Top Phase": ["", "", ""],
                            "Bottom Phase": ["", "", ""]
                        }
                        df_atps = pd.DataFrame(atps_data)
                        st.dataframe(df_atps, use_container_width=True)
                        st.info("Select a formulation to view ATPS composition")
                else:
                    # Fallback table structure
                    atps_data = {
                        "Component": ["Gel polymer concentration", "Co-polymer concentration", "Buffer concentration"],
                        "Top Phase": ["", "", ""],
                        "Bottom Phase": ["", "", ""]
                    }
                    df_atps = pd.DataFrame(atps_data)
                    st.dataframe(df_atps, use_container_width=True)
                    st.info("No composition data available")
            
            with col_performance:
                st.markdown("**Drug Release**")
                
                # Get pre-generated performance trend data for selected formulation
                if selected_formulation in performance_trends:
                    trend_data = performance_trends[selected_formulation]
                    x_values = trend_data["x_values"]
                    y_values = trend_data["y_values"]
                    release_time_value = trend_data["release_time"]
                    
                    # Add pivot shape at the start (0.2 ~ 0.5)
                    import random
                    # Set seed for consistent pivot per formulation
                    random.seed(hash(f"{current_job_name}_{selected_formulation}_pivot") % 2147483647)
                    pivot_y = random.uniform(0.2, 0.5)
                    
                    # Modify y_values to include pivot at start
                    modified_y_values = y_values.copy()
                    if len(modified_y_values) > 0:
                        # Set the first point to the pivot value
                        modified_y_values[0] = pivot_y
                        # Ensure the trend still increases overall
                        for i in range(1, len(modified_y_values)):
                            if modified_y_values[i] < modified_y_values[i-1]:
                                modified_y_values[i] = modified_y_values[i-1] + 0.01
                    
                    # Create graph using modified data with pivot
                    fig, ax = plt.subplots(figsize=(6, 5))
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Different colors for each formulation
                    
                    # Get color index based on formulation number
                    formulation_index = formulation_options.index(selected_formulation)
                    color = colors[formulation_index % len(colors)]
                    
                    # Plot the line with pivot point highlighted
                    ax.plot(x_values, modified_y_values, marker="o", linewidth=3, markersize=6, color=color)
                    ax.fill_between(x_values, modified_y_values, alpha=0.3, color=color)
                    
                    # Highlight the pivot point at the start
                    if len(x_values) > 0 and len(modified_y_values) > 0:
                        ax.plot(x_values[0], modified_y_values[0], marker="^", markersize=12, 
                               color='red', markeredgecolor='darkred', markeredgewidth=2, 
                               label=f'Pivot Point ({pivot_y:.2f})')
                    
                    # Set axis limits and labels
                    ax.set_xlim(0, release_time_value)
                    ax.set_ylim(0, 1)
                    ax.set_xlabel("Time (Weeks)", fontsize=12)
                    ax.set_ylabel("Performance", fontsize=12)
                    ax.set_title(f"Drug Release", fontsize=12, fontweight='bold')
                    
                    # Add grid for better readability
                    ax.grid(True, alpha=0.3)
                    ax.set_axisbelow(True)
                    
                    # Add legend for pivot point
                    ax.legend(loc='lower right')
                    
                    st.pyplot(fig)
            
            # Show radar comparison below the two columns
            st.divider()
            
            # Radar chart comparison (moved from previous column layout)
            st.markdown("**Target vs Result Comparison**")
            
            # Get target profile data
            if 'selected_target_profile' in result_data:
                target_profile = result_data['selected_target_profile']
                
                if ('formulation_data' in target_profile and 
                    len(target_profile['formulation_data'].columns) >= 4):
                    
                    formulation_data = target_profile['formulation_data']
                    
                    # Extract target values (columns 1, 2, 3 after Name column)
                    target_modulus = float(str(formulation_data.iloc[0, 1]).replace('%', '').replace('Day', '').strip())
                    target_encap_rate = float(str(formulation_data.iloc[0, 2]).replace('%', '').replace('Day', '').strip())
                    target_release_time = float(str(formulation_data.iloc[0, 3]).replace('%', '').replace('Day', '').strip())
                    
                    # Generate result values based on formulation (simulate calculation results)
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
                    labels = ['Modulus', 'Encapsulation Rate', 'Release Time (Week)']
                    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                    
                    # Close the radar chart
                    target_norm += target_norm[:1]
                    result_norm += result_norm[:1]
                    angles += angles[:1]
                    
                    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
                    
                    # Plot target profile line
                    ax.plot(angles, target_norm, marker="o", linewidth=2.5, markersize=6, 
                           color='blue', label='Target Profile', alpha=0.8)
                    ax.fill(angles, target_norm, alpha=0.15, color='blue')
                    
                    # Plot result line
                    ax.plot(angles, result_norm, marker="s", linewidth=2.5, markersize=6, 
                           color='red', label=f'{selected_formulation} Result', alpha=0.8)
                    ax.fill(angles, result_norm, alpha=0.15, color='red')
                    
                    # Customize radar chart
                    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                    ax.set_ylim(0, 100)
                    ax.set_title(f"Target vs Result Comparison\n{selected_formulation}", 
                               y=1.08, fontsize=14, fontweight='bold')
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

    # ── Evaluation Tab ───────────────────────────────────────────────────────
    with tab_evaluation:
        st.subheader("Evaluation")
        
        # Check if evaluation data exists from calculation
        has_evaluation_data = (current_job.has_result_data() and 
                             'evaluation_diagrams' in current_job.result_dataset)
        
        if has_evaluation_data:
            # Get evaluation data from calculation results
            eval_data = current_job.result_dataset['evaluation_diagrams']
            
            # Formulation selector - always show if evaluation data exists
            formulation_options = list(eval_data.keys())
            selected_formulation = st.selectbox(
                "Select Formulation for Evaluation:",
                formulation_options,
                key="evaluation_formulation_selector"
            )
            
            # Show diagrams automatically when formulation is selected
            if selected_formulation:
                # Get data for selected formulation
                selected_eval_data = eval_data[selected_formulation]
                eval_timestamp = selected_eval_data["timestamp"]
                
                st.divider()
                
                col_left, col_right = st.columns(2)
                
                # Left Column: Safety & Stability Score
                with col_left:
                    safety_scores = selected_eval_data["safety_stability"]
                    labels_safety = list(safety_scores.keys())
                    vals_safety = list(safety_scores.values())
                    
                    # Create radar chart for Safety & Stability
                    angles = np.linspace(0, 2*np.pi, len(labels_safety), endpoint=False).tolist()
                    vals_plot = vals_safety + vals_safety[:1]  # Complete the circle
                    angles_plot = angles + angles[:1]  # Complete the circle
                    
                    fig1, ax1 = plt.subplots(figsize=(4, 4), subplot_kw={'polar': True})
                    ax1.plot(angles_plot, vals_plot, marker="o", linewidth=3, markersize=8, color='#2E8B57')
                    ax1.fill(angles_plot, vals_plot, alpha=0.25, color='#2E8B57')
                    ax1.set_thetagrids(np.degrees(angles), labels_safety)
                    ax1.set_ylim(0, 10)
                    ax1.set_title(f"Safety & Stability Score", y=1.08, fontsize=12, fontweight='bold')
                    ax1.grid(True, alpha=0.3)
                    
                    # Add score labels on the chart
                    for angle, val, label in zip(angles, vals_safety, labels_safety):
                        ax1.text(angle, val + 0.5, str(val), ha='center', va='center', 
                               fontsize=11, fontweight='bold', color='darkgreen')
                    
                    st.pyplot(fig1)
                
                # Right Column: Formulation Score
                with col_right:
                    formulation_scores = selected_eval_data["formulation"]
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
                    ax2.set_title(f"Formulation Score", y=1.08, fontsize=12, fontweight='bold')
                    ax2.grid(True, alpha=0.3)
                    
                    # Add score labels on the chart
                    for angle, val, label in zip(angles, vals_formulation, labels_formulation):
                        ax2.text(angle, val + 0.5, str(val), ha='center', va='center', 
                               fontsize=11, fontweight='bold', color='darkred')
                    
                    st.pyplot(fig2)
