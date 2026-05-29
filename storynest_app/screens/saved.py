from __future__ import annotations

import streamlit as st

from storynest_app.state import _clear_generation_state
from storynest_app import components as ui


def saved_screen() -> None:
    result = st.session_state.save_result or {}
    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        if result.get("enjoyed"):
            st.markdown(
                "<div style='text-align:center;font-size:2.4rem;margin-top:1rem;'>✨</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<h2 style='text-align:center;'>Saved to your shelf</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='text-align:center;margin-bottom:1rem;opacity:0.8;'>"
                f"Rating: {ui.rating_stars(result['rating'])}</div>",
                unsafe_allow_html=True,
            )
            if result.get("path"):
                st.caption(f"Saved file: `{result['path']}`")
        else:
            st.markdown(
                "<div style='text-align:center;font-size:2.4rem;margin-top:1rem;'>🌒</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<h2 style='text-align:center;'>Story not saved</h2>"
                "<div style='text-align:center;opacity:0.75;'>"
                "No rating was recorded.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        another_col, shelf_col = st.columns(2)
        with another_col:
            if st.button("Create Another", type="primary", use_container_width=True, key="saved_another"):
                _clear_generation_state()
                st.session_state.screen = "request"
                st.rerun()
        with shelf_col:
            if st.button("Story Shelf", use_container_width=True, key="saved_shelf"):
                _clear_generation_state()
                st.session_state.screen = "library"
                st.rerun()
