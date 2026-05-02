import streamlit as st


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
        if submitted:
            if key == correct_answer:
                st.markdown(
                    f'<div style="background:#d4edda;border:2px solid #28a745;border-radius:8px;'
                    f'padding:10px 16px;margin-bottom:8px;font-weight:600;">✅ {key}. {text}</div>',
                    unsafe_allow_html=True,
                )
            elif key == user_answer:
                st.markdown(
                    f'<div style="background:#f8d7da;border:2px solid #dc3545;border-radius:8px;'
                    f'padding:10px 16px;margin-bottom:8px;font-weight:600;">❌ {key}. {text}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;'
                    f'padding:10px 16px;margin-bottom:8px;color:#6c757d;">{key}. {text}</div>',
                    unsafe_allow_html=True,
                )
        else:
            if st.button(
                f"{key}. {text}",
                key=f"opt_{question_number}_{key}",
                use_container_width=True,
            ):
                clicked = key

    return clicked
