import streamlit as st

st.set_page_config(
    page_title="QuizMind AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Auth sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    user = st.session_state.get("user")
    if user:
        st.markdown(f"👤 **{user['username']}**")
        if st.button("My Profile", use_container_width=True):
            st.session_state["screen"] = "profile"
            st.rerun()
        if st.button("Sign Out", use_container_width=True):
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
            st.session_state["screen"] = "start"
            st.rerun()
    else:
        st.markdown("Not signed in")
        if st.button("Sign In / Register", use_container_width=True):
            st.session_state["screen"] = "auth"
            st.rerun()

# ── Screen router ──────────────────────────────────────────────────────────────

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

elif screen == "auth":
    from frontend.pages.profile import render_auth_screen

    render_auth_screen()

elif screen == "profile":
    from frontend.pages.profile import render_profile_screen

    render_profile_screen()
