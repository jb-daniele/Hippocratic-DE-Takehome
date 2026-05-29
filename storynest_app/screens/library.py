from __future__ import annotations

import streamlit as st

from storynest_app.state import _begin_read, _begin_remix_from_library, _read_index_entries
from storynest_app import components as ui


def library_screen() -> None:
    st.title("Story Shelf")
    entries = _read_index_entries()
    if not entries:
        st.info("No saved stories yet.")
        if st.button("Create your first story", type="primary", key="shelf_create_first"):
            st.session_state.screen = "request"
            st.rerun()
        return

    distinct_categories = sorted(
        {entry.get("category_display_name") or entry.get("category_id") or "Story" for entry in entries}
    )
    filter_options = ["All categories", *distinct_categories]
    sort_options = ["Newest", "Highest rated"]

    filter_col, sort_col = st.columns([2, 1])
    with filter_col:
        chosen_category = st.selectbox(
            "Category",
            filter_options,
            index=filter_options.index(st.session_state.shelf_filter_category)
            if st.session_state.shelf_filter_category in filter_options
            else 0,
            key="shelf_filter_category_widget",
        )
        st.session_state.shelf_filter_category = chosen_category
    with sort_col:
        chosen_sort = st.selectbox(
            "Sort by",
            sort_options,
            index=sort_options.index(st.session_state.shelf_sort) if st.session_state.shelf_sort in sort_options else 0,
            key="shelf_sort_widget",
        )
        st.session_state.shelf_sort = chosen_sort

    if chosen_category != "All categories":
        entries = [
            entry
            for entry in entries
            if (entry.get("category_display_name") or entry.get("category_id")) == chosen_category
        ]

    if chosen_sort == "Highest rated":
        entries.sort(key=lambda entry: (entry.get("user_rating") or 0, entry.get("created_at", "")), reverse=True)
    else:
        entries.sort(key=lambda entry: entry.get("created_at", ""), reverse=True)

    if not entries:
        st.info("No stories match this filter yet.")
        return

    columns = st.columns(3)
    for index, entry in enumerate(entries):
        with columns[index % 3]:
            action = ui.shelf_tile(entry, key=f"tile_{entry['run_id']}")
            if action == "read":
                _begin_read(entry["run_id"])
            elif action == "remix":
                _begin_remix_from_library(entry["run_id"])
