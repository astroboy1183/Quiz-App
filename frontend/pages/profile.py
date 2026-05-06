import httpx
import streamlit as st

BACKEND = "http://localhost:8000"

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


def _post(path: str, payload: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = httpx.post(f"{BACKEND}{path}", json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get(path: str, token: str) -> dict:
    resp = httpx.get(
        f"{BACKEND}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _put(path: str, payload: dict, token: str) -> dict:
    resp = httpx.put(
        f"{BACKEND}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _go(screen: str) -> None:
    st.session_state["screen"] = screen
    st.rerun()


# ── Auth screen ────────────────────────────────────────────────────────────────


def render_auth_screen() -> None:
    st.title("🧠 QuizMind AI")
    st.markdown("Sign in to save your progress and track your history.")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Sign In", use_container_width=True, type="primary"):
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                try:
                    data = _post("/users/login", {"email": email, "password": password})
                    _store_session(data["access_token"])
                    _go("start")
                except httpx.HTTPStatusError as e:
                    st.error(e.response.json().get("detail", "Login failed."))
                except httpx.HTTPError:
                    st.error("Could not reach the server.")

        st.markdown("---")
        if st.button("Continue without signing in", use_container_width=True):
            _go("start")

    with tab_register:
        r_email = st.text_input("Email", key="reg_email")
        r_username = st.text_input("Username (3–30 chars)", key="reg_username")
        r_password = st.text_input(
            "Password (min 6 chars)", type="password", key="reg_password"
        )
        if st.button("Create Account", use_container_width=True, type="primary"):
            if not r_email or not r_username or not r_password:
                st.error("Please fill in all fields.")
            elif len(r_username) < 3:
                st.error("Username must be at least 3 characters.")
            elif len(r_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    data = _post(
                        "/users/register",
                        {
                            "email": r_email,
                            "username": r_username,
                            "password": r_password,
                        },
                    )
                    _store_session(data["access_token"])
                    _go("start")
                except httpx.HTTPStatusError as e:
                    st.error(e.response.json().get("detail", "Registration failed."))
                except httpx.HTTPError:
                    st.error("Could not reach the server.")


def _store_session(token: str) -> None:
    me = _get("/users/me", token)
    st.session_state["token"] = token
    st.session_state["user"] = me


# ── Profile screen ─────────────────────────────────────────────────────────────


def render_profile_screen() -> None:
    token = st.session_state.get("token")
    user = st.session_state.get("user", {})

    st.title(f"👤 {user.get('username', 'Profile')}")
    st.markdown(f"**Email:** {user.get('email', '')}")
    st.markdown("---")

    st.subheader("Preferences")
    st.caption("These pre-fill your quiz start screen.")

    topic_idx = TOPICS.index(user.get("preferred_topic", "Mixed"))
    diff_idx = DIFFICULTIES.index(user.get("preferred_difficulty", "Medium"))

    new_topic = st.selectbox("Preferred topic", TOPICS, index=topic_idx)
    new_diff = st.radio(
        "Preferred difficulty", DIFFICULTIES, index=diff_idx, horizontal=True
    )
    new_count = st.slider(
        "Default number of questions",
        min_value=5,
        max_value=20,
        value=user.get("question_count", 10),
        step=5,
    )

    if st.button("Save Preferences", type="primary"):
        try:
            updated = _put(
                "/users/me/settings",
                {
                    "preferred_topic": new_topic,
                    "preferred_difficulty": new_diff,
                    "question_count": new_count,
                },
                token,
            )
            st.session_state["user"] = updated
            st.success("Preferences saved!")
        except httpx.HTTPError:
            st.error("Failed to save preferences.")

    st.markdown("---")
    st.subheader("Quiz History")
    try:
        history = _get("/users/me/history?page=1&page_size=10", token)
        items = history.get("items", [])
        if not items:
            st.info("No quizzes yet — start one!")
        else:
            for item in items:
                acc = round(item["accuracy"] * 100, 1)
                st.markdown(
                    f"**{item['topic']}** · {item['difficulty']} · "
                    f"{item['score']}/{item['total_qs']} ({acc}%)"
                )
    except httpx.HTTPError:
        st.error("Could not load history.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Quiz", use_container_width=True):
            _go("start")
    with col2:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.pop("token", None)
            st.session_state.pop("user", None)
            _go("start")
