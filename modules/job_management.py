# Top section: Current Job Overview
    if st.session_state.get("current_job") and st.session_state.current_job in st.session_state.get("jobs", {}):
        current_job = st.session_state.jobs[st.session_state.current_job]
        
        st.markdown(f"## Current Job Status")
        st.markdown(f"**Name:** {st.session_state.current_job}")
        st.markdown(f"**Created:** {current_job.created_at}")
        
        # Save job to cloud section
        st.markdown("### 💾 Save job to cloud")

        if st.button("💾 Save Job Permanently", key="save_current_job", help="Save this job permanently"):
            success, result = save_job_to_file(current_job, st.session_state.current_job)
            if success:
                st.success(f"✅ Job '{st.session_state.current_job}' saved permanently!")
                st.info(f"📁 Saved to: {result}")
            else:
                st.error(f"❌ Failed to save job: {result}")
    else:
        st.warning("⚠️ No job currently selected. Create or select a job below.")
