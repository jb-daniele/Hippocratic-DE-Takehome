from __future__ import annotations

import streamlit as st

from storynest_app import components as ui


def cover_screen() -> None:
    package = st.session_state.package
    if package is None:
        st.session_state.screen = "home"
        st.rerun()
        return

    ui.cover_panel(package, rating=None)

    st.markdown("<div style='margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        if st.button("Start Reading", type="primary", use_container_width=True, key="cover_start"):
            st.session_state.page_index = 0
            st.session_state.reader_mode = "generation"
            st.session_state.read_view = None
            st.session_state.screen = "reader"
            st.rerun()
        with st.expander("Reviewer Details"):
            ui.reviewer_details(package, st.session_state.trace_id)
