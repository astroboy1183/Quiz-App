import streamlit as st

_S_CORRECT = (
    "background:#d4edda;border:2px solid #28a745;"
    "border-radius:8px;padding:10px 16px;margin-bottom:8px;font-weight:600;"
)
_S_WRONG = (
    "background:#f8d7da;border:2px solid #dc3545;"
    "border-radius:8px;padding:10px 16px;margin-bottom:8px;font-weight:600;"
)
_S_SELECTED = (
    "background:#e8f0fe;border:2px solid #4a90d9;"
    "border-radius:8px;padding:10px 16px;margin-bottom:8px;font-weight:600;"
)
_S_DIMMED = (
    "background:#f8f9fa;border:1px solid #dee2e6;"
    "border-radius:8px;padding:10px 16px;margin-bottom:8px;color:#6c757d;"
)


def _div(style: str, content: str) -> None:
    st.markdown(
        f'<div style="{style}">{content}</div>',
        unsafe_allow_html=True,
    )


def render_question_card(
    question_number: int,
    total: int,
    question_text: str,
    options: dict[str, str],
    submitted: bool,
    correct_answer: str | None,
    user_answer: str | None,
) -> str | None:
    """
    Renders a question with 4 option buttons.

    Returns the selected option key ("A"–"D") when the user clicks,
    or None if nothing was clicked this rerun.
    Buttons are disabled after submission.
    """
    st.markdown(f"### Question {question_number} of {total}")
    st.markdown(f"**{question_text}**")
    st.markdown("---")

    clicked = None

    for key, text in options.items():
        label = f"{key}. {text}"
        if submitted and correct_answer is not None:
            # Full feedback mode — used in the results answer review
            if key == correct_answer:
                _div(_S_CORRECT, f"✅ {label}")
            elif key == user_answer:
                _div(_S_WRONG, f"❌ {label}")
            else:
                _div(_S_DIMMED, label)
        elif submitted:
            # Neutral mode — answer recorded, feedback revealed at end
            if key == user_answer:
                _div(_S_SELECTED, f"👉 {label}")
            else:
                _div(_S_DIMMED, label)
        else:
            if st.button(
                label,
                key=f"opt_{question_number}_{key}",
                use_container_width=True,
            ):
                clicked = key

    return clicked
