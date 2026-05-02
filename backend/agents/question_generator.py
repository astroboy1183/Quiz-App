import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from backend.config import settings

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT = (
    "You are a quiz question generator. "
    "Return ONLY valid JSON — no markdown, no extra text.\n\n"
    "Generate {{count}} unique multiple-choice questions about "
    '"{topic}" at {difficulty} difficulty.\n\n'
    "Rules:\n"
    "- Each question has exactly 4 options labelled A, B, C, D.\n"
    "- Exactly one option is correct.\n"
    "- Questions must be distinct — no duplicates.\n"
    "- Difficulty guide: Easy = factual recall, "
    "Medium = applied knowledge, Hard = nuanced/analytical.\n\n"
    "Return a JSON array:\n"
    "[\n"
    "  {{\n"
    '    "question_text": "...",\n'
    '    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},\n'
    '    "correct_answer": "A",\n'
    '    "topic": "{topic}",\n'
    '    "difficulty": "{difficulty}"\n'
    "  }},\n"
    "  ...\n"
    "]"
)


class RawQuestion(BaseModel):
    question_text: str
    options: dict[str, str]
    correct_answer: str
    topic: str
    difficulty: str


async def generate_questions(
    topic: str, difficulty: str, count: int = 10
) -> list[RawQuestion]:
    prompt = _SYSTEM_PROMPT.format(topic=topic, difficulty=difficulty, count=count)

    for attempt in range(3):
        try:
            response = await _client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            raw = response.choices[0].message.content or ""

            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                questions_data = next(v for v in parsed.values() if isinstance(v, list))
            else:
                questions_data = parsed

            questions = [RawQuestion(**q) for q in questions_data]

            if len(questions) < count:
                raise ValueError(f"Expected {count} questions, got {len(questions)}")

            for q in questions:
                if set(q.options.keys()) != {"A", "B", "C", "D"}:
                    raise ValueError(
                        f"Question missing required options: {q.question_text}"
                    )
                if q.correct_answer not in q.options:
                    raise ValueError(
                        f"correct_answer not in options: {q.correct_answer}"
                    )

            return questions[:count]

        except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
            logger.warning(
                "[QuestionGenerator] Attempt %d failed: %s", attempt + 1, exc
            )
            if attempt == 2:
                raise RuntimeError(
                    "Failed to generate valid questions after 3 attempts"
                ) from exc

    raise RuntimeError("Unreachable")
