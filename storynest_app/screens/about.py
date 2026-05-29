from __future__ import annotations

import streamlit as st

from story_engine.categories import CATEGORIES


def about_screen() -> None:
    st.title("About StoryNest")
    st.markdown(
        "StoryNest is a local multi-agent bedtime story engine. It plans, writes, "
        "stitches, and judges each story before it reaches the reader."
    )

    st.markdown("### What makes a good bedtime story")
    st.markdown(
        "- **Calm pacing.** Small moments, quiet transitions, no sudden alarm.\n"
        "- **Concrete imagery.** Hands, objects, places, and small sounds a child can picture.\n"
        "- **A small problem, gently resolved.** Low stakes, a clear ending, no cliffhanger.\n"
        "- **Natural read-aloud rhythm.** Simple past tense, varied sentences, no moralizing wrap-up."
    )

    st.markdown("### Story archetypes")
    st.caption("StoryNest picks one of these from your request, or you can choose directly from Story settings.")
    for category in CATEGORIES:
        with st.container(border=True):
            st.markdown(f"**{category['display_name']}**")
            st.markdown(
                f"<span style='opacity:0.78;'>{category['description']}</span>",
                unsafe_allow_html=True,
            )

    st.markdown("### How a story is built")
    stages = [
        ("Classifier", "Reads the request and chooses one story archetype to guide the rest of the run."),
        ("Character Designer", "Builds character cards with a name, kind, pronouns, and two showable traits."),
        ("Arc Planner", "Lays out a gentle 4-scene arc with a small problem and a calm resolution."),
        ("Scene Planner", "Turns the arc into per-scene cards with setting, concrete beats, and dialogue cues."),
        ("Scene Writers", "Write each scene from its card, one at a time."),
        ("Scene Rewriter", "Targets any scene whose beats, dialogue, or ending image came out wrong, and rewrites only that scene."),
        ("Scene Stitcher", "Smooths the seams between scenes so the story reads as one piece."),
        ("Judges", "Independently check the finished story for safety, coherence, and language quality."),
        ("Polisher", "Makes surface-level prose fixes when a judge flags a polishable issue."),
        ("Title Writer", "Reads the finished story and writes a specific, child-friendly title."),
    ]
    for label, body in stages:
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.markdown(f"<span style='opacity:0.78;'>{body}</span>", unsafe_allow_html=True)

    st.markdown("### Save semantics")
    st.markdown(
        "- Stories are saved to your local shelf **only** when you ask to save them at the end of the reader.\n"
        "- Ratings are recorded only when a story is saved, and influence future inspiration selection.\n"
        "- All generation runs append events to a local trace log; reviewer details on the "
        "story cover replay that trace."
    )
