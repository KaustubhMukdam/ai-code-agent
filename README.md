# AI Code Agent

A secure, automatic code generation and grading platform with JWT authentication, analytics, and AI-powered review pipeline.  
**Local-Only Edition: Works fully on your machine, Docker/cloud not required!**

---

## Features

- **AI Code Generation** (Python, C++, Java, JS, C, Go)
- **Dual-Agent Quality Control**: Generation + Review/Grading
- **JWT Auth, Admin Panels, User Analytics**
- **Role-based Access (Admin/User)**
- **Code Execution: Local Docker-based sandbox**
- **REST API** built in FastAPI
- **Database Migrations** with Alembic
- **Free for local use** (no cloud billing/limits)
- **Streamlit UI** for the frontend

---

## Tech Stack

| Category     | Component                      |
| ------------ | ----------------------------- |
| Backend      | FastAPI, SQLAlchemy, Alembic  |
| AI/LLM       | LangGraph, Groq API (Llama 3) |
| Security     | JWT, Argon2, SlowAPI          |
| Execution    | Local Docker                  |
| Database     | SQLite (default) or Postgres  |
| Frontend     | Streamlit                     |

---

## Quick Start (Local Setup)

### Prerequisites

- Python 3.8+ (recommend 3.10+)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for code sandboxing, optional)
- Git

### 1. Clone & Set Up

```bash
git clone https://github.com/KaustubhMukdam/ai-code-agent.git
cd ai-code-agent

# Create virtual environment
python -m venv venv

# Activate:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your API keys, secrets, DB URL. (Default: SQLite OK!)

### 2. Apply Database Migrations

```bash
alembic upgrade head
```

### 3. Start Backend (API)

```bash
uvicorn app:app --reload
```

Visit http://localhost:8000/docs to test!

### 4. Start Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

Visit http://localhost:8501 to use app

---

## Configuration

### .env (example)

```bash
# AI/LLM
GROQ_API_KEY=your_groq_key

# DB (default: SQLite)
DATABASE_URL=sqlite:///./data/ai_code_agent.db
# For local Postgres: postgresql://postgres:yourpassword@localhost:5432/aiagent

# Security/auth
SECRET_KEY=your-secret-32chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Project Structure

```
ai-code-agent/
├── src/                # Agents, API, models, schemas, utils
├── alembic/            # Migrations
├── data/               # SQLite DB (if used)
├── frontend/           # Streamlit UI
├── tests/              # Unit/integration tests
├── app.py              # FastAPI entry
├── requirements.txt    # All dependencies
├── .env.example        # Template for .env
└── README.md
```

---

## API Docs & Testing

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Run all tests:**

```bash
pytest
```

---

## Security Best Practices

- Don't commit .env or secrets to git!
- Use strong, unique SECRET_KEY.
- Use Docker for code execution security if possible.
- SQLite is fine for dev; use Postgres for production/local scaling.

---

## Roadmap

- Backend API + Roles
- AI agent workflow
- Authentication/JWT
- Local Docker sandbox

---

## Troubleshooting

- **DB errors:** Check DATABASE_URL, ensure migrations are run.
- **Docker errors:** Ensure Docker Desktop is running if executing code in sandbox mode.

---

## License

MIT

---

**Made with ❤️ by Kaustubh Mukdam**