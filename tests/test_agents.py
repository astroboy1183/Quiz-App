"""Tests for agent logic that doesn't require a live DB or LLM."""

from backend.agents.answer_evaluator import evaluate_answer


class TestAnswerEvaluator:
    def test_correct_answer(self):
        assert evaluate_answer("A", "A") is True

    def test_wrong_answer(self):
        assert evaluate_answer("B", "A") is False

    def test_none_is_wrong(self):
        assert evaluate_answer(None, "A") is False

    def test_case_insensitive(self):
        assert evaluate_answer("a", "A") is True
        assert evaluate_answer("A", "a") is True

    def test_all_options(self):
        for opt in ["A", "B", "C", "D"]:
            assert evaluate_answer(opt, opt) is True
            others = [o for o in ["A", "B", "C", "D"] if o != opt]
            for wrong in others:
                assert evaluate_answer(wrong, opt) is False
