"""
AI Code Agent - Main Entry Point
"""

import asyncio
from src.utils.config import get_settings
from src.utils.logger import setup_logging, get_logger


# Setup
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


async def main():
    """Main application entry point"""
    logger.info(
        "AI Code Agent Starting",
        app_name=settings.app_name,
        environment=settings.environment,
        model=settings.groq_model,
        max_iterations=settings.max_iterations,
    )
    
    # Verify Groq API key
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        logger.error("GROQ_API_KEY not set! Please add it to .env file")
        return
    
    logger.info("✅ Configuration loaded successfully")
    logger.info(f"✅ Input directory: {settings.input_dir}")
    logger.info(f"✅ Output directory: {settings.output_dir}")
    logger.info(f"✅ Supported languages: {settings.allowed_languages}")
    
    # TODO: We'll add agent initialization in next steps
    logger.info("🚀 Ready to build the agent!")


if __name__ == "__main__":
    asyncio.run(main())
