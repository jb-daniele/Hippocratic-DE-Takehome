from __future__ import annotations

import html

import streamlit as st

from storynest_app import components as ui


def reader_screen() -> None:
    read_only = st.session_state.reader_mode == "read_only"

    if read_only:
        read_view = st.session_state.read_view
        if not read_view:
            st.session_state.screen = "library"
            st.rerun()
            return
        title = read_view["title"]
        pages = read_view["pages"]
    else:
        package = st.session_state.package
        if package is None:
            st.session_state.screen = "home"
            st.rerun()
            return
        title = package.story.title
        pages = package.pages

    if not pages:
        st.info("This story has no pages to display.")
        return

    total = len(pages)
    page_index = min(st.session_state.page_index, total - 1)
    st.session_state.page_index = page_index

    spacer_l, body, spacer_r = st.columns([1, 4, 1])
    with body:
        st.markdown(
            f"<h2 style='text-align:center;margin-bottom:0.4rem;'>{html.escape(title)}</h2>",
            unsafe_allow_html=True,
        )
        ui.page_progress(page_index, total)
        page_html = html.escape(pages[page_index]).replace("\n", "<br><br>")
        st.markdown(
            f"<div style='max-width: 720px; margin: 1.5rem auto; font-size: 1.18rem; "
            f"line-height: 1.78;'>{page_html}</div>",
            unsafe_allow_html=True,
        )

        prev_col, back_col, next_col = st.columns([1, 1, 1])
        with prev_col:
            if st.button("← Previous", disabled=page_index == 0, use_container_width=True, key="reader_prev"):
                st.session_state.page_index = max(0, page_index - 1)
                st.rerun()
        with back_col:
            if read_only:
                if st.button("Back to Shelf", use_container_width=True, key="reader_back_shelf"):
                    st.session_state.screen = "library"
                    st.rerun()
            else:
                if st.button("Back to Cover", use_container_width=True, key="reader_back_cover"):
                    st.session_state.screen = "cover"
                    st.rerun()
        with next_col:
            if page_index >= total - 1:
                label = "Done" if read_only else "Finish"
                if st.button(label, type="primary", use_container_width=True, key="reader_finish"):
                    st.session_state.screen = "library" if read_only else "completion"
                    st.rerun()
            else:
                if st.button("Next →", type="primary", use_container_width=True, key="reader_next"):
                    st.session_state.page_index = min(total - 1, page_index + 1)
                    st.rerun()

        with st.expander("View full story"):
            full_text = "\n\n".join(pages)
            st.markdown(
                f"<div style='max-width:720px;margin:0 auto;line-height:1.7;'>"
                f"{html.escape(full_text).replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )
