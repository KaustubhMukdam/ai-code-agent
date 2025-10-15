# AI Code Generation Agent

Production-ready AI agent that generates, executes, validates, and documents code across multiple programming languages.

## Features

✅ Multi-language code generation (Python, JavaScript, Java, C, C++, Go)  
✅ LLM-powered with Groq (Llama 3.3 70B)  
✅ Secure Docker-based code execution  
✅ Real-time output capture  
✅ Comprehensive validation (upcoming)  
✅ Automated documentation generation (upcoming)  

## Tech Stack

- **LangGraph**: Agent orchestration
- **Groq API**: Code generation
- **Docker**: Secure code execution
- **Python**: Core implementation
- **FastAPI**: REST API (upcoming)

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Groq API key
4. Build Docker images: See `docker/` folder
5. Run: `python test_graph.py`

## Status

🟢 Phase 1-3 Complete  
🟡 Phase 4-8 In Progress

## License

MIT
