from __future__ import annotations

import streamlit as st

from storynest_app.state import _clear_generation_state, GENERIC_FAILURE_MESSAGE, message_for_failure
from story_engine import trace
from story_engine.errors import RunFailed
from story_engine.pipeline import run


def generating_screen() -> None:
    st.title("Writing your story")
    st.caption(
        "This usually takes 2–4 minutes. Multiple agents plan, write, stitch, and "
        "judge the story; revisions may extend it further."
    )
    with st.spinner("Planning, writing, stitching, and judging…"):
        try:
            with trace.Run(st.session_state.trace_id):
                package = run(
                    st.session_state.pending_request,
                    st.session_state.pending_options,
                    remix_source=st.session_state.pending_remix_source,
                )
        except RunFailed as exc:
            _clear_generation_state()
            st.session_state["fail_message"] = message_for_failure(exc.failure_category)
            st.session_state.screen = "error"
            st.rerun()
        except Exception:
            _clear_generation_state()
            st.session_state["fail_message"] = GENERIC_FAILURE_MESSAGE
            st.session_state.screen = "error"
            st.rerun()
    st.session_state.package = package
    st.session_state.screen = "cover"
    st.rerun()
