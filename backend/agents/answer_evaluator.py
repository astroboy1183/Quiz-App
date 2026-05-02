import logging

logger = logging.getLogger(__name__)


def evaluate_answer(
    selected_option: str | None,
    correct_answer: str,
) -> bool:
    """
    Returns True if selected_option matches correct_answer.
    None (timeout) is always False.
    """
    if selected_option is None:
        return False
    return selected_option.strip().upper() == correct_answer.strip().upper()
