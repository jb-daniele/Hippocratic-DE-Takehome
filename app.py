from __future__ import annotations

import streamlit as st

from storynest_app.screens.about import about_screen
from storynest_app.screens.completion import completion_screen
from storynest_app.screens.cover import cover_screen
from storynest_app.screens.error import error_screen
from storynest_app.screens.generating import generating_screen
from storynest_app.screens.home import home_screen
from storynest_app.screens.library import library_screen
from storynest_app.screens.reader import reader_screen
from storynest_app.screens.remix import remix_screen
from storynest_app.screens.request import request_screen
from storynest_app.screens.saved import saved_screen
from storynest_app.state import STABLE_SCREENS, _clear_generation_state, _init_state
from story_engine import persistence


# --- Sidebar -----------------------------------------------------------------


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.4rem;font-weight:700;margin-bottom:0.2rem;'>StoryNest</div>"
            "<div style='font-size:0.85rem;margin-bottom:1rem;opacity:0.7;'>Gentle bedtime stories</div>",
            unsafe_allow_html=True,
        )
        current = st.session_state.screen
        in_flow = current not in STABLE_SCREENS

        if st.button("Home", key="nav_home", use_container_width=True, disabled=in_flow):
            _clear_generation_state()
            st.session_state.screen = "home"
            st.rerun()
        if st.button("Story Shelf", key="nav_shelf", use_container_width=True, disabled=in_flow):
            st.session_state.screen = "library"
            st.rerun()
        if st.button("About", key="nav_about", use_container_width=True, disabled=in_flow):
            st.session_state.screen = "about"
            st.rerun()
        if st.session_state.get("library_selected_run_id") and not in_flow:
            if st.button("Remix Story", key="nav_remix", use_container_width=True):
                if not st.session_state.get("saved_story"):
                    st.session_state.saved_story = persistence.load_for_remix(
                        st.session_state.library_selected_run_id
                    )
                st.session_state.screen = "remix"
                st.rerun()

        if in_flow:
            st.caption("Sidebar paused while a story is in progress.")

        st.markdown(
            "<hr style='margin:1rem 0;border:none;border-top:1px solid rgba(128,128,128,0.25);'>",
            unsafe_allow_html=True,
        )
        st.caption("Stories are saved only when you choose to keep them.")


def main() -> None:
    st.set_page_config(page_title="StoryNest", page_icon="🌙", layout="wide")
    _init_state()
    _render_sidebar()

    screen = st.session_state.screen
    if screen == "home":
        home_screen()
    elif screen == "library":
        library_screen()
    elif screen == "request":
        request_screen()
    elif screen == "generating":
        generating_screen()
    elif screen == "error":
        error_screen()
    elif screen == "cover":
        cover_screen()
    elif screen == "reader":
        reader_screen()
    elif screen == "completion":
        completion_screen()
    elif screen == "saved":
        saved_screen()
    elif screen == "remix":
        remix_screen()
    elif screen == "about":
        about_screen()
    else:
        st.session_state.screen = "home"
        st.rerun()


if __name__ == "__main__":
    main()
