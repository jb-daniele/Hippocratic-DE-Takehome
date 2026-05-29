from __future__ import annotations

import streamlit as st

from storynest_app.state import _clear_generation_state


def error_screen() -> None:
    message = st.session_state.get("fail_message") or (
        "Something went wrong while writing your story. Please try again."
    )
    st.title("Story generation didn't finish")
    st.error(message)
    if st.button("Back to menu", type="primary", use_container_width=True, key="error_back_home"):
        _clear_generation_state()
        st.session_state.pop("fail_message", None)
        st.session_state.library_selected_run_id = None
        st.session_state.saved_story = None
        st.session_state.screen = "home"
        st.rerun()
