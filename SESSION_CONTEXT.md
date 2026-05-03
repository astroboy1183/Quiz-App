# QuizMind AI — Session Context
> Bring this file into any Claude conversation to pick up exactly where we left off.
> Last updated: May 2026 | Sprint 1 fully closed

---

## 1. Who is building this

An intermediate-level developer upskilling toward an **AI/ML Engineer** role.
Goal: land a new job by building a strong, real-world AI portfolio project.
QuizMind AI is the centrepiece of that portfolio.

---

## 2. What we are building

**QuizMind AI** — an AI-powered competitive learning platform.
- Phase 1: Web app (Streamlit + FastAPI) — current phase
- Phase 2: Mobile app (React Native) — same FastAPI backend, only the client changes

Full feature set is documented in `QUIZMIND_CONTEXT.md` in the project root.

---

## 3. Current project state

### Sprint status

| Sprint | Title | Status |
|---|---|---|
| Sprint 1 | Core Quiz Engine | ✅ COMPLETE |
| Sprint 2 | User Accounts & Auth | ⬜ Next |
| Sprint 3 | AI Tutor Agent | ⬜ Pending |
| Sprint 4 | Learning Path Agent | ⬜ Pending |
| Sprint 5 | Progress Dashboard | ⬜ Pending |
| Sprint 6 | Multiplayer Mode | ⬜ Pending |
| Sprint 7 | Leaderboard System | ⬜ Pending |
| Sprint 8 | Docker, CI & Polish | ⬜ Pending |

### Sprint 1 Definition of Done checklist

| Item | Status |
|---|---|
| All 7 stories coded | ✅ |
| 13/13 automated tests passing | ✅ |
| Ruff lint — 0 errors | ✅ |
| Black format — clean | ✅ |
| Code pushed to GitHub (`main` branch) | ✅ |
| Manual end-to-end test passed | ✅ |

### GitHub repository
- URL: `https://github.com/astroboy1183/Quiz-App`
- Branch: `main` (all Sprint 1 work merged here directly)
- Remote: SSH (`git@github.com:astroboy1183/Quiz-App.git`)
- SSH key set up at `~/.ssh/id_ed25519` for `jayanthapalla@gmail.com`

---

## 4. What Sprint 1 built

### The data flow

```
Browser (Streamlit)
       │  HTTP
       ▼
FastAPI Router  ──►  OrchestratorAgent (logs session events)
       │
       ├──►  QuestionGeneratorAgent  ──►  OpenAI API (GPT-4o)
       │         (validates with Pydantic, retries 3x on bad output)
       │
       ├──►  AnswerEvaluatorAgent  (pure function, no LLM)
       │
       ├──►  QuizService  ──►  PostgreSQL
       │         (create session, save answers, compute score)
       │
       └──►  Returns JSON  ──►  Streamlit renders it
```

### API endpoints built

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/quiz/start` | Creates session in DB, generates N questions from OpenAI, returns `session_id` |
| GET | `/quiz/{id}/question/{n}` | Returns question N from the in-memory cache |
| POST | `/quiz/{id}/answer` | Looks up correct answer from cache, evaluates, saves to DB |
| GET | `/quiz/{id}/results` | Computes final score + accuracy + topic breakdown, updates session row |
| GET | `/health` | Health check |

### Key files and their purpose

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app entry point, CORS, router registration |
| `backend/config.py` | Loads `.env` via pydantic-settings |
| `backend/database.py` | Async SQLAlchemy engine + `get_db` dependency |
| `backend/models/user.py` | `users` table |
| `backend/models/session.py` | `quiz_sessions` table |
| `backend/models/answer.py` | `answers` table |
| `backend/schemas/quiz.py` | All Pydantic request/response schemas |
| `backend/agents/orchestrator.py` | Stub — logs lifecycle events. Full LangGraph in Sprint 3 |
| `backend/agents/question_generator.py` | Calls OpenAI, validates JSON output, retries on failure |
| `backend/agents/answer_evaluator.py` | Pure function: `evaluate_answer(selected, correct) → bool` |
| `backend/services/quiz_service.py` | DB operations: create session, record answer, finalise session |
| `backend/routers/quiz.py` | Wires endpoints → agents → service |
| `frontend/app.py` | Streamlit screen router (start → quiz → results) |
| `frontend/pages/quiz.py` | All three screens in one file |
| `frontend/components/timer.py` | Countdown bar, auto-submits on timeout |
| `frontend/components/question_card.py` | Option buttons, neutral highlight during quiz, green/red in review |
| `frontend/components/score_card.py` | Score metrics + Plotly topic accuracy bar chart |
| `alembic/versions/f062e3697c94_initial_tables.py` | Migration: creates users, quiz_sessions, answers |
| `tests/test_agents.py` | Unit tests for answer evaluator |
| `tests/test_services.py` | DB logic tests using in-memory SQLite |
| `tests/test_routers.py` | Full HTTP flow tests, mocks OpenAI |

### Database tables (Sprint 1)

- `users` — created but not yet used (Sprint 2 wires auth)
- `quiz_sessions` — one row per quiz (topic, difficulty, score, accuracy, time_taken)
- `answers` — one row per question answered (question_text, correct_answer, user_answer, is_correct, time_taken)

---

## 5. Architectural decisions made

### Question storage — current behaviour
- Questions are **NOT stored** in the database
- Generated fresh from OpenAI on every `POST /quiz/start`
- Cached in a Python dict (`_question_cache`) in the router for the duration of the session
- `correct_answer` is never sent to the frontend during the quiz — backend looks it up from cache on submit (prevents client spoofing)
- Only the answer rows store question text (inside `answers.question_text`)
- Every quiz start costs one OpenAI API call

### Question bank — deferred to v2
**Decision: implement after full app is deployed to Play Store (v2).**
- Sprint 2 (user auth) is needed first — without user IDs, can't track per-user seen questions
- Purely additive when we do it — one new table, one new function, one line change in the router

### Question generation — current behaviour
- Model: GPT-4o (configurable via `LLM_MODEL` env var)
- Format: JSON mode (`response_format={"type": "json_object"}`) — model must return `{"questions": [...]}`
- Retry: up to 3 attempts on malformed output
- Validation: Pydantic `RawQuestion` model checks structure, option keys, correct_answer validity

### In-memory question cache
- `_question_cache: dict[str, list]` in `backend/routers/quiz.py`
- Keyed by `session_id`
- Cleared when `GET /quiz/{id}/results` is called
- **Note:** Replaced by Redis in Sprint 6 for multiplayer support

### Quiz UX — deferred feedback
- Per-question correct/wrong feedback is **NOT shown during the quiz** (to avoid demotivating users)
- After selecting, the chosen option shows a **neutral blue highlight** (👉), others fade out
- Full green/red answer review is shown on the **results screen** as expandable cards

### Timer design
- 30-second countdown per question using wall-clock time (`time.time()`)
- Timer key scoped to `{session_id}_q{q_num}` — prevents stale timestamps from old sessions causing instant-zero timer on new quizzes
- Auto-submits `None` answer on timeout

### Async everywhere
- All DB operations use `async/await` via SQLAlchemy async engine
- FastAPI handles concurrent requests without blocking

---

## 6. Technology stack — quick reference

| Technology | Role |
|---|---|
| FastAPI | REST API server |
| Pydantic v2 | Request/response validation + LLM output validation |
| SQLAlchemy (async) | ORM — Python instead of raw SQL |
| PostgreSQL 16 | Production database (port 5433 on host to avoid conflict) |
| Alembic | Database migrations |
| Redis 7 | Cache + pub/sub (used fully from Sprint 6) |
| OpenAI SDK v1 | GPT-4o API calls |
| LangGraph | Multi-agent orchestration (Sprint 3+) |
| Streamlit | Web UI (Phase 1) |
| React Native | Mobile UI (Phase 2) |
| Docker Compose | Local dev environment |
| Poetry | Python dependency management |
| Pytest + pytest-asyncio | Automated testing |
| Ruff + Black | Linting and formatting |
| aiosqlite | SQLite async driver (tests only) |

---

## 7. How to run the app locally

### Prerequisites
- Docker Desktop running
- OpenAI API key in `.env`

### Commands
```bash
# 1. Start PostgreSQL and Redis
docker-compose up -d postgres redis

# 2. Run DB migrations
alembic upgrade head

# 3. Start the backend (in one terminal)
uvicorn backend.main:app --reload

# 4. Start the frontend (in another terminal — PYTHONPATH is required)
PYTHONPATH=/home/jayanth/Desktop/QuizMind-AI streamlit run frontend/app.py
```

### URLs
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Run tests (no Docker needed)
```bash
python3 -m pytest tests/ -v
```

---

## 8. Bugs fixed during Sprint 1 manual E2E test

| Bug | Root cause | Fix |
|---|---|---|
| `StopIteration` → 500 on `/quiz/start` | `next(generator)` inside async raises `RuntimeError` | Used `next(..., None)` with explicit check |
| GPT returns `{"error": "..."}` for 10+ questions | `{{count}}` in prompt template produced literal `{count}` after `.format()` | Fixed to `{count}` |
| GPT returns dict with no list | Prompt said "return array" but `json_object` mode forces a dict | Changed prompt to return `{"questions": [...]}` |
| `KeyError: 'correct_answer'` on answer submit | `correct_answer` not in `Question` schema (intentional) but frontend read it from question dict | Backend looks up from cache; frontend reads from submit response |
| Timer shows 0s immediately on new quiz | Timer key `q1_start` from previous session lingered in session_state; `reset_timer()` was removing wrong key | Scoped timer key to `{session_id}_q{q_num}` |
| Options flash white after selecting | `_S_DIMMED` used `background:#f8f9fa` (near-white); rerender delay showed intermediate button state | Changed to `transparent`; added `st.rerun()` immediately after submit |
| Selected option shows white | `_S_SELECTED` used `background:#e8f0fe` (light blue) | Changed to `rgba(74,144,217,0.2)` (dark semi-transparent blue) |

---

## 9. Sprint 2 — what's coming next

**Goal:** User registration, login, JWT authentication, profile page, quiz history.

**Key tasks:**
- `User` model already exists (from Sprint 1 migration) — just needs the auth layer on top
- `POST /users/register` and `POST /users/login` endpoints
- JWT middleware to protect quiz routes
- Streamlit login/register page
- Public profile page (username, badges, stats)
- User settings (preferred topic, difficulty, question count, timer)
- `GET /users/{id}/history` — paginated quiz history

**Dependencies on Sprint 1:**
- `quiz_sessions.user_id` column exists but is currently `NULL` for all sessions
- Sprint 2 will wire the logged-in user's ID into `POST /quiz/start` so sessions are attributed

---

## 10. Important notes for next session

1. **SSH is configured** — `git push` works without passwords
2. **The `users` table exists** in the DB schema (from Sprint 1 migration) but no auth logic is wired yet
3. **OrchestratorAgent is a stub** — it only logs. Full LangGraph wiring happens in Sprint 3
4. **"View AI Tutor" button** on the results screen is visible but disabled — activates in Sprint 3
5. **Port 5433** — Docker PostgreSQL maps to host port 5433 (not 5432) to avoid conflict with local Postgres
6. **PYTHONPATH required** — Streamlit must be started with `PYTHONPATH=/home/jayanth/Desktop/QuizMind-AI`

---

## 11. Folder structure

```
quizmind-ai/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── redis_client.py         (empty — Sprint 6)
│   ├── chroma_client.py        (empty — Sprint 3)
│   ├── agents/
│   │   ├── orchestrator.py     (stub — Sprint 3)
│   │   ├── question_generator.py
│   │   ├── answer_evaluator.py
│   │   ├── tutor.py            (empty — Sprint 3)
│   │   ├── path_planner.py     (empty — Sprint 4)
│   │   └── stats_aggregator.py (empty — Sprint 7)
│   ├── routers/
│   │   ├── quiz.py             (complete)
│   │   ├── users.py            (empty — Sprint 2)
│   │   ├── multiplayer.py      (empty — Sprint 6)
│   │   ├── leaderboard.py      (empty — Sprint 7)
│   │   └── progress.py         (empty — Sprint 5)
│   ├── models/
│   │   ├── user.py             (complete)
│   │   ├── session.py          (complete)
│   │   ├── answer.py           (complete)
│   │   └── leaderboard.py      (empty — Sprint 7)
│   ├── schemas/
│   │   ├── quiz.py             (complete)
│   │   ├── user.py             (empty — Sprint 2)
│   │   └── leaderboard.py      (empty — Sprint 7)
│   ├── services/
│   │   ├── quiz_service.py     (complete)
│   │   ├── user_service.py     (empty — Sprint 2)
│   │   └── leaderboard_service.py (empty — Sprint 7)
│   └── workers/
│       └── tasks.py            (empty — Sprint 6)
├── frontend/
│   ├── app.py                  (complete)
│   ├── pages/
│   │   ├── quiz.py             (complete)
│   │   ├── tutor.py            (empty — Sprint 3)
│   │   ├── learning_path.py    (empty — Sprint 4)
│   │   ├── progress.py         (empty — Sprint 5)
│   │   ├── leaderboard.py      (empty — Sprint 7)
│   │   ├── multiplayer.py      (empty — Sprint 6)
│   │   └── profile.py          (empty — Sprint 2)
│   └── components/
│       ├── question_card.py    (complete)
│       ├── score_card.py       (complete)
│       └── timer.py            (complete)
├── tests/
│   ├── test_agents.py          (complete — 5 tests)
│   ├── test_routers.py         (complete — 5 tests)
│   └── test_services.py        (complete — 3 tests)
├── alembic/
│   └── versions/
│       └── f062e3697c94_initial_tables.py
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── pyproject.toml
├── alembic.ini
├── .env.example
└── QUIZMIND_CONTEXT.md
```

---

*Context file updated after Sprint 1 manual E2E test and bug fixes | QuizMind AI v0.1.0*
