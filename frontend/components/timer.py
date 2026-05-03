import time

import streamlit as st


def render_timer(duration_seconds: int, key: str = "timer") -> int:
    """
    Renders a countdown progress bar and returns seconds remaining.
    Uses st.session_state to track start time so it survives reruns.
    Caller must call st.rerun() in a loop to animate the bar.

    Returns:
        seconds_remaining (int). 0 means expired.
    """
    start_key = f"{key}_start"

    if start_key not in st.session_state:
        st.session_state[start_key] = time.time()

    elapsed = time.time() - st.session_state[start_key]
    remaining = max(0, duration_seconds - int(elapsed))

    fraction = remaining / duration_seconds
    color = "green" if fraction > 0.5 else ("orange" if fraction > 0.25 else "red")

    st.markdown(
        f"""
        <div style="margin-bottom:8px;">
            <span style="font-size:1.1rem;font-weight:600;color:{color};">
                ⏱ {remaining}s remaining
            </span>
        </div>
        <div style="background:#e0e0e0;border-radius:6px;height:10px;width:100%;">
            <div style="background:{color};width:{fraction*100:.1f}%;height:10px;
                        border-radius:6px;transition:width 0.5s ease;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return remaining


def reset_timer(key: str = "timer") -> None:
    start_key = f"{key}_start"
    st.session_state.pop(start_key, None)
