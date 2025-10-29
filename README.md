# AI Code Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)

Production-ready SaaS platform for secure, automatic code generation and grading — with user authentication, admin analytics, and a robust dual-AI pipeline.

## 🌟 Features

### Core Capabilities
- **🤖 Secure AI Code Generation** - Supports Python, C++, Java, JavaScript, C, and Go
- **🔍 Dual Agent Quality Control** - Review/Billet system ensures code quality and accuracy
- **🔐 Enterprise Authentication** - JWT-based auth with Argon2 password hashing
- **📊 Analytics Dashboard** - Admin dashboard with personal analytics for each user
- **👥 Multi-User Support** - Role-based access control (Admin, User)
- **🐳 Sandboxed Execution** - Docker-based code execution for security
- **⚡ REST API** - Full-featured FastAPI backend with auto-generated docs
- **🗄️ Database Migrations** - Alembic-powered schema management
- **💳 Billing Ready** - Stripe integration prepared (database + minimal code)
- **☁️ Cloud Native** - Scales instantly to Render, AWS, or any cloud platform

### The Dual-AI Pipeline

Our unique **Review/Billet Agent System** provides enterprise-grade code quality:

1. **Generation Agent** - Creates initial code based on user requirements
2. **Review Agent** - Analyzes, validates, and grades the generated code
3. **Quality Assurance** - Ensures best practices, security, and correctness
4. **Feedback Loop** - Continuous improvement through agent collaboration

## 🛠️ Tech Stack

| Category | Component |
|----------|-----------|
| **Backend** | FastAPI, SQLAlchemy, Alembic |
| **Agents/LLM** | LangGraph, Groq API (Llama 3) |
| **Security** | JWT, Argon2, SlowAPI (rate limiting) |
| **Execution** | Docker (sandboxed) |
| **Database (Dev)** | SQLite |
| **Database (Prod)** | PostgreSQL (managed) |
| **Infrastructure** | Docker, Docker Compose |
| **Frontend*** | Streamlit (planned), React/Next.js (roadmap) |

*Frontend currently in development

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/KaustubhMukdam/ai-code-agent.git
cd ai-code-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys and secrets (NEVER commit this file!)
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Database
DATABASE_URL=sqlite:///./data/ai_code_agent.db  # Dev
# DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Prod

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (optional)
STRIPE_SECRET_KEY=your_stripe_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_pub_key_here
```

### 3. Run with Docker Compose

```bash
# Start all services (PostgreSQL + API)
docker-compose up --build

# API will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### 4. Apply Database Migrations

```bash
# Run migrations
alembic upgrade head

# Create a new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"
```

## 📁 Project Structure

```
ai-code-agent/
├── src/
│   ├── agents/          # AI agent logic (Review/Billet)
│   ├── api/             # FastAPI routes
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── utils/           # Helper functions
│   └── security/        # Auth & security
├── alembic/             # Database migrations
│   ├── versions/        # Migration scripts
│   └── env.py
├── data/                # Input/output & SQLite (dev)
├── frontend/            # Streamlit app (planned)
├── tests/               # Unit & integration tests
├── app.py               # FastAPI entry point
├── docker-compose.yml   # Multi-service orchestration
├── Dockerfile.backend   # Backend container
├── Dockerfile.frontend  # Frontend container
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md
```

## ☁️ Cloud Deployment

### Backend (Render.com)

1. **Create Web Service**
   - Link your GitHub repository to Render
   - Select `Dockerfile.backend` as the build file
   - Set build command: `docker build -f Dockerfile.backend -t backend .`

2. **Configure Environment Variables**
   - Navigate to Render Dashboard → Your Service → Environment
   - Add all variables from `.env.example`
   - Never commit secrets to version control!

3. **Setup PostgreSQL**
   - Add Render's Managed PostgreSQL service
   - Copy the internal `DATABASE_URL` to your environment variables
   - Run migrations: `alembic upgrade head`

4. **Deploy**
   - Push to your main branch
   - Render auto-deploys on every commit
   - Monitor logs via Render dashboard

### Frontend (Streamlit Cloud)

**Option 1: Streamlit Cloud (Recommended for MVP)**
```bash
# Create separate repo for frontend or use monorepo
cd frontend
git init
git remote add origin <your-frontend-repo>

# Deploy via Streamlit Cloud dashboard
# Set backend URL: https://<your-backend>.onrender.com
```

**Option 2: Render (Full Control)**
- Create another Web Service
- Select `Dockerfile.frontend`
- Configure `BACKEND_API_URL` environment variable

## 🔌 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

```
POST   /api/auth/register     # Register new user
POST   /api/auth/login        # Login and get JWT token
POST   /api/code/generate     # Generate code from prompt
GET    /api/code/history      # Get generation history
POST   /api/code/execute      # Execute code in sandbox
GET    /api/admin/analytics   # Admin dashboard data
GET    /api/user/stats        # Personal analytics
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🔒 Security Best Practices

### Production Checklist
- ✅ Use managed PostgreSQL (never SQLite in production)
- ✅ Enable HTTPS (Render provides free SSL)
- ✅ Set strong `SECRET_KEY` (min 32 characters)
- ✅ Use environment variables for all secrets
- ✅ Enable rate limiting (SlowAPI configured)
- ✅ Docker sandboxing for code execution
- ✅ JWT token expiration configured
- ✅ Argon2 password hashing
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ CORS properly configured

### Never Commit
- `.env` files
- API keys or tokens
- Database credentials
- Private keys

## 🐛 Troubleshooting

### Common Issues

**Docker build fails**
```bash
# Clear Docker cache
docker-compose down -v
docker system prune -a
docker-compose up --build
```

**Database connection errors**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Verify DATABASE_URL format
# PostgreSQL: postgresql://user:password@host:5432/database
# SQLite: sqlite:///./data/ai_code_agent.db
```

**Migration errors**
```bash
# Reset migrations (development only!)
rm -rf alembic/versions/*
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Port already in use**
```bash
# Change port in docker-compose.yml or:
docker-compose down
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
```

## 🗺️ Roadmap

- ✅ Backend API + Database (Production Ready)
- ✅ Dual-AI Agent System
- ✅ JWT Authentication
- ✅ Docker Sandboxing
- 🟡 Streamlit Frontend (In Progress)
- 🟡 React/Next.js UI (Planned)
- 🟡 Stripe Billing Integration (90% Complete)
- ⬜ WebSocket Support for Real-time Updates
- ⬜ Code Collaboration Features
- ⬜ Advanced Analytics & Insights
- ⬜ API Rate Limiting Tiers
- ⬜ Multi-language Support for UI

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Keep commits atomic and meaningful

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

**Kaustubh Mukdam**
- GitHub: [@KaustubhMukdam](https://github.com/KaustubhMukdam)
- Repository: [ai-code-agent](https://github.com/KaustubhMukdam/ai-code-agent)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI agent orchestration
- [Groq](https://groq.com/) - Lightning-fast LLM inference
- [Render](https://render.com/) - Simple cloud deployment

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/KaustubhMukdam/ai-code-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/KaustubhMukdam/ai-code-agent/discussions)
- **Email**: kaustubh@example.com (Update with your actual email)

---

⭐ **Star this repo** if you find it helpful!

Made with ❤️ by [Kaustubh Mukdam](https://github.com/KaustubhMukdam)