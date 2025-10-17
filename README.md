# AI Assignment Code Pipeline

Production-ready AI-powered code generation SaaS platform with multi-user support, authentication, and automated document generation.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## 🚀 Features

### Core AI Pipeline

- ✅ **Dual-Agent System**: Generator + Reviewer AI agents for code quality
- ✅ **Multi-Language Support**: Python, C++, Java, JavaScript, C, Go
- ✅ **Secure Execution**: Docker-based sandboxed code testing
- ✅ **Smart Parsing**: Automatic question extraction from text files
- ✅ **Document Generation**: Professional .docx output with formatting
- ✅ **Error Recovery**: Automatic retry logic with feedback loops

### Production Features

- ✅ **REST API**: FastAPI with auto-generated documentation
- ✅ **JWT Authentication**: Secure token-based user system
- ✅ **Multi-User Support**: User isolation and data privacy
- ✅ **Rate Limiting**: API protection (10 jobs/hour per user)
- ✅ **Database Migrations**: Alembic for schema management
- ✅ **Admin Dashboard**: System statistics and user management
- ✅ **Analytics**: Personal usage tracking and metrics

### Enterprise Ready

- ✅ **Subscription Tiers**: Free, Pro, Enterprise (database ready)
- ✅ **Billing Integration**: Stripe-ready payment system
- ✅ **Usage Tracking**: Token consumption and cost monitoring
- ✅ **Scalable Architecture**: Production-grade database schema

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI, SQLAlchemy, Alembic |
| **AI/LLM** | LangGraph, Groq API (Llama 3.3 70B) |
| **Security** | JWT, Argon2, SlowAPI (rate limiting) |
| **Execution** | Docker, multi-language containers |
| **Documents** | python-docx, custom formatting |
| **Database** | SQLite (dev), PostgreSQL (prod) |

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker
- Groq API key ([Get one here](https://console.groq.com/))

### Setup

```bash
# 1. Clone repository
git clone https://github.com/KaustubhMukdam/ai-code-agent.git
cd ai-code-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Initialize database
alembic upgrade head

# 6. Start server
uvicorn app:app --reload
```

### Access

- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin/stats (requires admin user)

## 🎯 Quick Start

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass123"
  }'
```

### 2. Login & Get Token

```bash
curl -X POST "http://localhost:8000/token" \
  -F "username=testuser" \
  -F "password=securepass123"
```

### 3. Submit Assignment

```bash
curl -X POST "http://localhost:8000/submit-assignment" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@assignment.txt"
```

### 4. Check Status

```bash
curl "http://localhost:8000/status/{job_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Download Result

```bash
curl "http://localhost:8000/download/{job_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o result.docx
```

## 📁 Project Structure

```text
ai-code-agent/
├── src/
│   ├── agent/          # AI agent logic
│   │   ├── nodes.py    # Generator, Reviewer, Executor
│   │   ├── graph.py    # LangGraph workflow
│   │   └── state.py    # State management
│   ├── api/            # FastAPI endpoints
│   │   ├── models.py   # Database models
│   │   ├── auth.py     # JWT authentication
│   │   ├── admin.py    # Admin endpoints
│   │   └── rate_limit.py
│   ├── utils/          # Utilities
│   │   ├── executor.py # Docker code execution
│   │   ├── doc_generator.py
│   │   └── input_parser.py
├── alembic/            # Database migrations
├── docker/             # Dockerfile for languages
├── data/               # Database & files
├── app.py              # Main FastAPI app
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🔒 Security

- **JWT Tokens**: 24-hour expiry, HS256 algorithm
- **Password Hashing**: Argon2 (OWASP recommended)
- **Rate Limiting**: SlowAPI protection on all endpoints
- **Docker Isolation**: Code executes in sandboxed containers
- **SQL Injection**: Protected via SQLAlchemy ORM
- **Input Validation**: Pydantic models for all requests

## 📊 API Endpoints

### Authentication

- `POST /register` - Create new user
- `POST /token` - Login (get JWT token)
- `GET /me` - Get current user info

### Assignments

- `POST /submit-assignment` - Upload assignment file
- `GET /status/{job_id}` - Check job status
- `GET /download/{job_id}` - Download result document
- `GET /my-jobs` - List all your jobs

### Analytics

- `GET /analytics/usage` - Personal usage statistics

### Admin (requires admin role)

- `GET /admin/stats` - System-wide statistics
- `GET /admin/users` - List all users
- `GET /admin/jobs` - View all jobs
- `POST /admin/users/{id}/toggle-active` - Enable/disable user

## 🗄️ Database Schema

### Users Table

- Authentication (username, email, password)
- Subscription (tier, start/end dates)
- Usage tracking (jobs, tokens, spending)
- Quotas (monthly limits)

### Jobs Table

- Status tracking (queued, processing, done, error)
- Metrics (processing time, tokens, iterations)
- Cost tracking
- File paths (input/output)

### Billing Records (ready for Stripe)

- Transactions (charges, refunds, subscriptions)
- Stripe payment IDs

## 🔄 Database Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## 📈 Status & Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1-6 | Core AI Pipeline | ✅ Complete |
| 7 | Production Backend | ✅ Complete |
| 8 | Frontend UI | 🟡 Planned |
| 9 | Billing Integration | 🟡 Ready |
| 10 | Cloud Deployment | 🟡 Ready |

## 🎨 Coming Soon

- 🖥️ **Web Dashboard**: React/Next.js UI
- 💳 **Stripe Billing**: Automated payment processing
- 📊 **Analytics Charts**: Usage graphs and insights
- 🌐 **Cloud Deployment**: AWS/Railway hosting
- 📧 **Email Notifications**: Job completion alerts
- 🔔 **Webhooks**: Integration with external systems

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

**Kaustubh Devidas Mukdam**

Built with ❤️ using FastAPI, LangGraph, and Groq

*October 2025*

## 🙏 Acknowledgments

- [LangGraph](https://www.langchain.com/langgraph) - Agent orchestration
- [Groq](https://groq.com/) - Fast LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations

---

⭐ If this project helped you, consider giving it a star!