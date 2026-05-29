from __future__ import annotations

import streamlit as st

from storynest_app.state import _begin_generation, _options_from_request_form


def request_screen() -> None:
    st.title("Create a story")
    st.caption("Describe the wish for tonight's read-aloud.")

    prompt_col, settings_col = st.columns([3, 2])
    with prompt_col:
        wish = st.text_area(
            "What should tonight's story be about?",
            key="request_text",
            height=190,
            placeholder="A sleepy otter who lost his favorite rock...",
        )
        submitted = st.button(
            "Create Story",
            type="primary",
            disabled=not wish.strip(),
            use_container_width=True,
            key="request_submit",
        )

    with settings_col:
        with st.container(border=True):
            st.markdown("**Story settings**")
            options = _options_from_request_form()

    if submitted:
        _begin_generation(wish.strip(), options)
