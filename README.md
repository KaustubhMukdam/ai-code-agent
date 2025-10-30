# 🤖 Project 6/20 – AI Code Agent

*Part of my **100 Days of Code – Portfolio Project Series***

🚀 **AI Code Agent** is a secure, automatic code generation and grading platform powered by intelligent dual AI agents for both **generation and review**.  
It's designed for developers, educators, and learners who want **on-device, privacy-friendly** code automation — no cloud dependencies required!

🧠 **Local-Only Edition** — works fully offline on your machine (no Docker cloud billing or external servers).

🔗 **GitHub Repo:** [AI Code Agent](https://github.com/KaustubhMukdam/ai-code-agent)

---

## ✨ Features

- ⚙️ **AI Code Generation** in Python, C++, Java, JS, C, and Go  
- 🧩 **Dual-Agent Workflow:** Generation + Automated Review/Grading  
- 🔐 **JWT Authentication** with Role-based Access (Admin/User)  
- 🧭 **Admin Dashboard & Analytics** for insights and monitoring  
- 🧱 **Local Docker Sandbox** for secure code execution  
- 🚀 **FastAPI REST Backend** for modular API design  
- 📊 **Database Migrations** using Alembic + SQLAlchemy ORM  
- 💡 **Streamlit Frontend** for seamless user experience  
- 💻 **Free & Offline-First** – No cloud usage, no hidden API costs  

---

## 🛠 Tech Stack

| Layer | Components |
| :----- | :---------- |
| **Backend** | FastAPI, SQLAlchemy, Alembic |
| **AI / LLM** | LangGraph, Groq API (Llama 3) |
| **Security** | JWT, Argon2, SlowAPI |
| **Execution** | Local Docker sandbox |
| **Database** | SQLite (default) / PostgreSQL |
| **Frontend** | Streamlit |

---

## 🚀 Getting Started (Local Setup)

### Prerequisites

- Python **3.8+** (Recommended 3.10+)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) *(optional but recommended)*
- Git

### 1️⃣ Clone & Setup Environment

```bash
git clone https://github.com/KaustubhMukdam/ai-code-agent.git
cd ai-code-agent

# Create virtual environment
python -m venv venv

# Activate it:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
```

🧩 Edit `.env` with your API keys, secrets, and database URL.  
(Default SQLite works out of the box.)

### 2️⃣ Apply Database Migrations

```bash
alembic upgrade head
```

### 3️⃣ Start Backend (API)

```bash
uvicorn app:app --reload
```

Visit 👉 http://localhost:8000/docs to test Swagger API.

### 4️⃣ Start Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

Access UI 👉 http://localhost:8501

---

## ⚙️ Configuration (.env Example)

```bash
# AI/LLM
GROQ_API_KEY=your_groq_api_key

# Database (Default: SQLite)
DATABASE_URL=sqlite:///./data/ai_code_agent.db
# For Postgres: postgresql://postgres:password@localhost:5432/aiagent

# Security / Auth
SECRET_KEY=your-secret-32chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📂 Folder Structure

```
ai-code-agent/
├── src/                # Core logic (agents, schemas, models, utils)
├── alembic/            # Database migrations
├── data/               # SQLite database (if used)
├── frontend/           # Streamlit UI files
├── tests/              # Unit & integration tests
├── app.py              # FastAPI entry point
├── requirements.txt    # Python dependencies
├── .env.example        # Template environment file
└── README.md
```

---

## 🧠 Learning Outcomes

Through this project, I learned how to:

- Design a secure full-stack AI system integrating LLMs with real-time code execution
- Implement JWT authentication and role-based access control
- Work with FastAPI + Streamlit for unified dev workflows
- Architect modular systems with local Docker sandboxing
- Optimize developer experience (DX) with a clean API and UI

---

## 🔍 API Docs & Testing

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Run all tests:**

```bash
pytest
```

---

## 🔒 Security Best Practices

- Never commit `.env` or secret keys to Git.
- Use a strong `SECRET_KEY` and unique JWT signing algorithm.
- For untrusted code, run Docker sandbox mode for isolation.
- SQLite works great for development — use Postgres for production.

---

## 🚧 Roadmap

- Backend API & Auth
- Dual-agent AI workflow
- Streamlit UI

---

## 💡 Troubleshooting

- **Database Errors** → Check `DATABASE_URL` & migrations.
- **Docker Issues** → Ensure Docker Desktop is running.
- **JWT Expiry Issues** → Increase token duration in `.env`.

---

## 📝 License

This project is open-sourced under the **MIT License**.

---

## 👨‍💻 Author

**Kaustubh Mukdam**

- GitHub: [@KaustubhMukdam](https://github.com/KaustubhMukdam)
- LinkedIn: [Kaustubh Mukdam](https://www.linkedin.com/in/kaustubh-mukdam)

⭐ If you found this project useful, consider giving it a star on GitHub!