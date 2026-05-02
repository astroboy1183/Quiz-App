import time

import httpx
import streamlit as st

from frontend.components.question_card import render_question_card
from frontend.components.score_card import (
    render_score_card,
    render_topic_breakdown_chart,
)
from frontend.components.timer import render_timer, reset_timer

BACKEND = "http://localhost:8000"
TIMER_SECONDS = 30

TOPICS = [
    "Science",
    "History",
    "Geography",
    "Sports",
    "Technology",
    "Arts",
    "Politics",
    "Pop Culture",
    "Mathematics",
    "Mixed",
]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _post(path: str, payload: dict) -> dict:
    resp = httpx.post(f"{BACKEND}{path}", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _get(path: str) -> dict:
    resp = httpx.get(f"{BACKEND}{path}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def _go(screen: str) -> None:
    st.session_state["screen"] = screen
    st.rerun()


# ── Start screen (S1-01 + S1-04) ─────────────────────────────────────────────


def render_start_screen() -> None:
    st.title("🧠 QuizMind AI")
    st.markdown("Test your knowledge with AI-generated questions.")
    st.markdown("---")

    topic = st.selectbox("Choose a topic", TOPICS, index=TOPICS.index("Mixed"))
    difficulty = st.radio("Difficulty", DIFFICULTIES, index=1, horizontal=True)
    total_qs = st.slider(
        "Number of questions", min_value=5, max_value=20, value=10, step=5
    )

    if st.button("🚀 Start Quiz", use_container_width=True, type="primary"):
        with st.spinner("Generating your quiz…"):
            try:
                data = _post(
                    "/quiz/start",
                    {
                        "topic": topic,
                        "difficulty": difficulty,
                        "total_qs": total_qs,
                    },
                )
            except httpx.HTTPError as e:
                st.error(f"Could not start quiz: {e}")
                return

        # Initialise quiz session state
        st.session_state.update(
            {
                "session_id": data["session_id"],
                "topic": data["topic"],
                "difficulty": data["difficulty"],
                "total_qs": data["total_qs"],
                "current_q": 1,
                "current_question": None,
                "submitted": False,
                "user_answer": None,
                "answer_time": TIMER_SECONDS,
                "answers_log": [],  # list of answer dicts for local tracking
            }
        )
        _go("quiz")


# ── Quiz screen (S1-02, S1-03, S1-05) ────────────────────────────────────────


def render_quiz_screen() -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        _go("start")

    q_num = st.session_state["current_q"]
    total = st.session_state["total_qs"]

    # Load question from backend if not yet loaded for this question number
    if st.session_state.get("current_question") is None:
        reset_timer()
        try:
            q_data = _get(f"/quiz/{session_id}/question/{q_num}")
        except httpx.HTTPError as e:
            st.error(f"Failed to load question: {e}")
            return
        st.session_state["current_question"] = q_data
        st.session_state["submitted"] = False
        st.session_state["user_answer"] = None

    q = st.session_state["current_question"]
    submitted = st.session_state["submitted"]

    # Progress bar
    st.progress((q_num - 1) / total, text=f"Question {q_num} of {total}")

    # Timer (S1-05)
    remaining = render_timer(TIMER_SECONDS, key=f"q{q_num}")

    # Auto-submit on timeout
    if remaining == 0 and not submitted:
        _submit_answer(session_id, q, selected=None, time_taken=TIMER_SECONDS)

    # Question card (S1-02, S1-03)
    clicked = render_question_card(
        question_number=q_num,
        total=total,
        question_text=q["question_text"],
        options=q["options"],
        submitted=submitted,
        correct_answer=q.get("correct_answer") if submitted else None,
        user_answer=st.session_state["user_answer"],
    )

    if clicked and not submitted:
        elapsed = TIMER_SECONDS - remaining
        _submit_answer(session_id, q, selected=clicked, time_taken=elapsed)

    # Feedback message
    if submitted:
        if st.session_state.get("last_correct"):
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Wrong. Correct answer: **{q['correct_answer']}**")

        st.markdown("---")
        if q_num < total:
            if st.button("Next Question →", use_container_width=True, type="primary"):
                st.session_state["current_q"] += 1
                st.session_state["current_question"] = None
                reset_timer()
                st.rerun()
        else:
            if st.button("See Results 🏆", use_container_width=True, type="primary"):
                _fetch_and_store_results(session_id)
                _go("results")
    else:
        # Keep rerunning every second to animate the timer
        time.sleep(1)
        st.rerun()


def _submit_answer(
    session_id: str, q: dict, selected: str | None, time_taken: int
) -> None:
    try:
        resp = _post(
            f"/quiz/{session_id}/answer",
            {
                "question_number": st.session_state["current_q"],
                "question_text": q["question_text"],
                "selected_option": selected,
                "correct_answer": q["correct_answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "time_taken": time_taken,
            },
        )
        st.session_state["submitted"] = True
        st.session_state["user_answer"] = selected
        st.session_state["last_correct"] = resp["is_correct"]
        st.session_state["answer_time"] = time_taken
    except httpx.HTTPError as e:
        st.error(f"Failed to submit answer: {e}")


def _fetch_and_store_results(session_id: str) -> None:
    try:
        results = _get(f"/quiz/{session_id}/results")
        st.session_state["results"] = results
    except httpx.HTTPError as e:
        st.error(f"Failed to fetch results: {e}")


# ── Results screen (S1-06) ────────────────────────────────────────────────────


def render_results_screen() -> None:
    results = st.session_state.get("results")
    if not results:
        _go("start")

    st.title("🏆 Quiz Complete!")
    st.markdown("---")

    render_score_card(
        score=results["score"],
        total_qs=results["total_qs"],
        accuracy=results["accuracy"],
        time_taken=results["time_taken"],
        topic=results["topic"],
        difficulty=results["difficulty"],
    )

    st.markdown("---")
    render_topic_breakdown_chart(results.get("topic_breakdown", []))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Again", use_container_width=True):
            for key in [
                "session_id",
                "current_q",
                "current_question",
                "results",
                "submitted",
                "user_answer",
                "answers_log",
            ]:
                st.session_state.pop(key, None)
            _go("start")
    with col2:
        st.button(
            "📚 View AI Tutor",
            use_container_width=True,
            disabled=True,
            help="Available in Sprint 3",
        )
