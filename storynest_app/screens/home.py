from __future__ import annotations

import streamlit as st


def home_screen() -> None:
    st.markdown(
        "<div style='text-align:center;margin:2rem 0 0.5rem 0;'>"
        "<div style='font-size:3rem;font-weight:700;letter-spacing:-0.02em;'>StoryNest</div>"
        "<div style='font-size:1.15rem;margin-top:0.3rem;opacity:0.8;'>"
        "Gentle bedtime stories, generated and read page by page."
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin:2rem auto;max-width:520px;'>", unsafe_allow_html=True)
    create_col, shelf_col = st.columns(2)
    with create_col:
        if st.button("Create Story", type="primary", use_container_width=True, key="home_create"):
            st.session_state.screen = "request"
            st.rerun()
    with shelf_col:
        if st.button("Browse Story Shelf", use_container_width=True, key="home_shelf"):
            st.session_state.screen = "library"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<h3 style='text-align:center;margin-top:3rem;margin-bottom:1.4rem;font-weight:600;'>"
        "How it works</h3>",
        unsafe_allow_html=True,
    )
    steps = [
        ("1", "Choose settings", "Pick a story mode and an optional main character."),
        ("2", "Generate", "Multiple agents plan, write, stitch, and judge the story."),
        ("3", "Read", "Flip through a paginated reader built for bedtime."),
        ("4", "Keep or skip", "Save the story to your shelf if you'd like to read it again."),
    ]
    cols = st.columns(4, gap="medium")
    for col, (number, title, body) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div style='text-align:center;padding:1.6rem 1rem;border-radius:14px;
                            background:rgba(128,128,128,0.08);
                            border:1px solid rgba(128,128,128,0.18);height:100%;'>
                  <div style='width:48px;height:48px;border-radius:50%;
                              background:linear-gradient(135deg,#5c6bc0,#3949ab);
                              color:white;display:flex;align-items:center;justify-content:center;
                              font-weight:700;font-size:1.25rem;margin:0 auto 0.9rem auto;
                              box-shadow:0 2px 6px rgba(57,73,171,0.25);'>{number}</div>
                  <div style='font-weight:600;font-size:1.02rem;margin-bottom:0.45rem;'>{title}</div>
                  <div style='font-size:0.88rem;line-height:1.5;opacity:0.78;'>{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
