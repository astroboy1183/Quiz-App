# QuizMind AI

An AI-powered quiz platform that generates multiple-choice questions on any topic using GPT-4o. Built as a portfolio project targeting an AI/ML Engineer role.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Pydantic v2 |
| Database | PostgreSQL 16 (async SQLAlchemy) |
| Cache | Redis 7 |
| AI | OpenAI GPT-4o |
| Orchestration | LangGraph (Sprint 3+) |
| Migrations | Alembic |
| Testing | Pytest + pytest-asyncio |

## Features (Sprint 1)

- AI-generated multiple-choice questions on 10 topics at 3 difficulty levels
- 30-second countdown timer per question with auto-submit on timeout
- Deferred feedback — correct/wrong answers revealed only at the end
- Score, accuracy, and per-topic breakdown on the results screen
- Full answer review with expandable question cards after the quiz

## Project Roadmap

| Sprint | Feature | Status |
|---|---|---|
| 1 | Core Quiz Engine | ✅ Complete |
| 2 | User Accounts & Auth | ⬜ Next |
| 3 | AI Tutor Agent | ⬜ Pending |
| 4 | Learning Path Agent | ⬜ Pending |
| 5 | Progress Dashboard | ⬜ Pending |
| 6 | Multiplayer Mode | ⬜ Pending |
| 7 | Leaderboard System | ⬜ Pending |
| 8 | Docker, CI & Polish | ⬜ Pending |

## Getting Started

### Prerequisites

- Docker Desktop
- Python 3.11+
- Poetry
- An OpenAI API key

### Setup

```bash
# 1. Clone the repo
git clone git@github.com:astroboy1183/Quiz-App.git
cd Quiz-App

# 2. Install dependencies
poetry install

# 3. Create your .env file (copy .env.example and fill in your keys)
cp .env.example .env

# 4. Start PostgreSQL and Redis
docker-compose up -d postgres redis

# 5. Run database migrations
alembic upgrade head

# 6. Start the backend
uvicorn backend.main:app --reload

# 7. Start the frontend (in a second terminal)
PYTHONPATH=$(pwd) streamlit run frontend/app.py
```

### URLs

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Run Tests

```bash
python3 -m pytest tests/ -v
```

No Docker needed for tests — they use an in-memory SQLite database.
