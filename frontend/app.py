import streamlit as st

st.set_page_config(
    page_title="QuizMind AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Route between screens via st.session_state["screen"]
if "screen" not in st.session_state:
    st.session_state["screen"] = "start"

screen = st.session_state["screen"]

if screen == "start":
    from frontend.pages.quiz import render_start_screen

    render_start_screen()
elif screen == "quiz":
    from frontend.pages.quiz import render_quiz_screen

    render_quiz_screen()
elif screen == "results":
    from frontend.pages.quiz import render_results_screen

    render_results_screen()
