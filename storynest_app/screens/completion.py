from __future__ import annotations

import html

import streamlit as st

from story_engine import persistence, trace


def completion_screen() -> None:
    package = st.session_state.package
    if package is None:
        st.session_state.screen = "home"
        st.rerun()
        return

    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        st.markdown(
            "<div style='text-align:center;margin-top:1rem;'>"
            "<div style='font-size:2.4rem;'>🌙</div>"
            "<h2 style='margin-bottom:0.3rem;'>How was tonight's story?</h2>"
            "<div style='margin-bottom:1.2rem;opacity:0.75;'>"
            f"<i>{html.escape(package.story.title)}</i></div></div>",
            unsafe_allow_html=True,
        )

        enjoyed_answer = st.radio(
            "Do you want to save this story?",
            ["Yes", "No"],
            index=None,
            horizontal=True,
            key="completion_enjoyed",
        )
        rating = st.radio(
            "Rating",
            [1, 2, 3, 4, 5],
            index=2,
            horizontal=True,
            format_func=lambda n: "★" * n,
            key="completion_rating",
        )
        st.caption("Ratings shape future story inspiration. Rating is only recorded if you save the story.")

        disabled = enjoyed_answer is None
        action_col, back_col = st.columns([2, 1])
        with action_col:
            if st.button(
                "Save and Continue",
                type="primary",
                disabled=disabled,
                use_container_width=True,
                key="completion_save",
            ):
                enjoyed = enjoyed_answer == "Yes"
                if enjoyed:
                    with trace.Run(st.session_state.trace_id):
                        trace.event("agent.persist", enjoyed=True, rating=rating)
                        paths = persistence.persist_story(package, package.classification)
                        persistence.record_user_rating(paths["run_id"], rating)
                    st.session_state.save_result = {
                        "enjoyed": True,
                        "rating": rating,
                        "path": f"stories/{paths['run_id']}/story.html",
                    }
                else:
                    st.session_state.save_result = {"enjoyed": False, "rating": None, "path": None}
                st.session_state.screen = "saved"
                st.rerun()
        with back_col:
            if st.button("Back to Reader", use_container_width=True, key="completion_back"):
                st.session_state.screen = "reader"
                st.rerun()
