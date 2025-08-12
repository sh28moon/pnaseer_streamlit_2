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
            
            # Three column layout for ATPS Composition, Drug Release, and Target vs Result
            col_atps, col_performance, col_radar = st.columns(3)
            
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
                    release_time_value = trend_data["release_time"]
                    
                    # Generate logarithmic diminishingly increasing curve
                    import random
                    # Set seed for consistent curve per formulation
                    random.seed(hash(f"{current_job_name}_{selected_formulation}_drug_release") % 2147483647)
                    
                    # Parameters for logarithmic curve
                    start_value = random.uniform(0.0, 0.1)  # Start between 0.0 ~ 0.1
                    max_value = random.uniform(0.6, 0.7)    # End not exceeding 0.7
                    
                    # Create logarithmic curve: y = start + (max - start) * log(1 + ax) / log(1 + a*max_x)
                    # where 'a' controls the curve steepness
                    a = 5.0  # Steepness parameter
                    max_x = max(x_values) if x_values else release_time_value
                    
                    # Generate logarithmic y values
                    log_y_values = []
                    for x in x_values:
                        if x == 0:
                            y = start_value
                        else:
                            # Logarithmic function for diminishing increase
                            normalized_x = x / max_x
                            log_factor = np.log(1 + a * normalized_x) / np.log(1 + a)
                            y = start_value + (max_value - start_value) * log_factor
                        log_y_values.append(y)
                    
                    # Add small random noise to make it more realistic
                    noise_factor = 0.01
                    for i in range(len(log_y_values)):
                        noise = random.uniform(-noise_factor, noise_factor)
                        log_y_values[i] = max(0, min(0.7, log_y_values[i] + noise))
                    
                    # Ensure the curve is monotonically increasing
                    for i in range(1, len(log_y_values)):
                        if log_y_values[i] < log_y_values[i-1]:
                            log_y_values[i] = log_y_values[i-1] + 0.001
                    
                    # Add pivot point highlighting at the start
                    pivot_y = log_y_values[0] if log_y_values else start_value
                    
                    # Create graph using logarithmic curve
                    fig, ax = plt.subplots(figsize=(4, 3.3))  # Reduced size by 2/3
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Different colors for each formulation
                    
                    # Get color index based on formulation number
                    formulation_index = formulation_options.index(selected_formulation)
                    color = colors[formulation_index % len(colors)]
                    
                    # Plot the logarithmic curve
                    ax.plot(x_values, log_y_values, marker="o", linewidth=2, markersize=4, color=color)  # Reduced line and marker size
                    ax.fill_between(x_values, log_y_values, alpha=0.3, color=color)
                    
                    # Highlight the pivot point at the start
                    if len(x_values) > 0 and len(log_y_values) > 0:
                        ax.plot(x_values[0], log_y_values[0], marker="^", markersize=8, 
                               color='red', markeredgecolor='darkred', markeredgewidth=1.5, 
                               label=f'Start Point ({pivot_y:.3f})')
                    
                    # Set axis limits and labels with smaller font
                    ax.set_xlim(0, release_time_value)
                    ax.set_ylim(0, 0.75)  # Slightly above 0.7 for better visualization
                    ax.set_xlabel("Time (Weeks)", fontsize=9)  # Reduced font size
                    ax.set_ylabel("Drug Release", fontsize=9)   # Reduced font size
                    ax.set_title(f"Drug Release (Log Curve)", fontsize=10, fontweight='bold')  # Reduced font size
                    
                    # Add grid for better readability
                    ax.grid(True, alpha=0.3)
                    ax.set_axisbelow(True)
                    
                    # Add legend for start point with smaller font
                    ax.legend(loc='lower right', fontsize=8)  # Reduced font size
                    
                    # Adjust tick label sizes
                    ax.tick_params(labelsize=8)  # Reduced tick label size
                    
                    st.pyplot(fig)
            
            with col_radar:
                st.markdown("**Target vs Result**")
                
                # Get target profile data
                if 'selected_target_profile' in result_data:
                    target_profile = result_data['selected_target_profile']
                    
                    if ('formulation_data' in target_profile and 
                        len(target_profile['formulation_data'].columns) >= 4):
                        
                        formulation_data = target_profile['formulation_data']
                        
                        # Generate result values based on formulation (simulate calculation results)
                        import random
                        formulation_index = formulation_options.index(selected_formulation)
                        
                        # Set seed for consistent results per formulation
                        random.seed(hash(f"{current_job_name}_{selected_formulation}_radar") % 2147483647)
                        
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
                        ax.set_yticks([0, 30, 60, 90, 120])
                        ax.set_yticklabels(['0%', '30%', '60%', '90%', '120%'], fontsize=6)
                        
                        ax.set_title(f"Target vs Result\n{selected_formulation}", 
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
