import plotly.graph_objects as go
import streamlit as st


def render_score_card(
    score: int,
    total_qs: int,
    accuracy: float,
    time_taken: int,
    topic: str,
    difficulty: str,
) -> None:
    accuracy_pct = accuracy * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{score}/{total_qs}")
    col2.metric("Accuracy", f"{accuracy_pct:.1f}%")
    col3.metric("Time", f"{time_taken}s")

    st.markdown(f"**Topic:** {topic} &nbsp;|&nbsp; **Difficulty:** {difficulty}")


def render_topic_breakdown_chart(breakdown: list[dict]) -> None:
    if not breakdown:
        return

    topics = [b["topic"] for b in breakdown]
    accuracies = [round(b["accuracy"] * 100, 1) for b in breakdown]
    colors = ["#28a745" if a >= 60 else "#dc3545" for a in accuracies]

    fig = go.Figure(
        go.Bar(
            x=topics,
            y=accuracies,
            marker_color=colors,
            text=[f"{a}%" for a in accuracies],
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Accuracy by Topic",
        yaxis=dict(range=[0, 100], title="Accuracy %"),
        xaxis_title="Topic",
        showlegend=False,
        height=300,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
