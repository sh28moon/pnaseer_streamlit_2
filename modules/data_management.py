# pages/data_management.py
import streamlit as st
import pandas as pd

def show():
    st.header("Data Management")

    # Top‐level subtabs
    tab_common, tab_polymer = st.tabs(["Common API", "Polymers"])

    # Ensure both dataset stores exist
    for key in ("common_api_datasets", "polymer_datasets"):
        if key not in st.session_state:
            st.session_state[key] = {}

    def render_subpage(tab, session_key):
        with tab:
            # ── 1st row: Import & Select ─────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Import Dataset")
                uploaded = st.file_uploader(
                    "Upload CSV",
                    type=["csv"],
                    key=f"{session_key}_import"
                )
                if uploaded:
                    df = pd.read_csv(uploaded)
                    st.session_state[session_key][uploaded.name] = df
                    st.success(f"Loaded dataset: {uploaded.name}")

            with col2:
                st.subheader("Select Dataset")
                names = list(st.session_state[session_key].keys())
                if names:
                    selected = st.selectbox(
                        "Choose dataset",
                        names,
                        key=f"{session_key}_select"
                    )
                else:
                    st.info("No datasets imported yet.")
                    return  # nothing more to show

            # ── 2nd row: Summary & Edit/Save ────────────────────────
            col3, col4 = st.columns([2, 2])
            with col3:
                st.subheader("Dataset Summary")
                df_sel = st.session_state[session_key][selected]
                st.dataframe(df_sel, use_container_width=True)

            with col4:
                st.subheader("Edit & Save")
                # a) Add External Data
                ext = st.file_uploader(
                    "Add External Data (CSV)",
                    type=["csv"],
                    key=f"{session_key}_ext"
                )
                if ext:
                    df_ext = pd.read_csv(ext)
                    df_cur = st.session_state[session_key][selected]
                    df_new = pd.concat([df_cur, df_ext], ignore_index=True)
                    st.session_state[session_key][selected] = df_new
                    st.success("External data appended.")

                # b) Save Data
                if st.button("Save Dataset", key=f"{session_key}_save"):
                    # Persist logic goes here
                    st.success(f"Dataset '{selected}' saved.")

                # c) Remove dataset
                if st.button("Remove Dataset", key=f"{session_key}_remove"):
                    st.session_state[session_key].pop(selected, None)
                    st.success(f"Removed Dataset: {selected}")

    # Render each subpage
    render_subpage(tab_common, "common_api_datasets")
    render_subpage(tab_polymer, "polymer_datasets")
