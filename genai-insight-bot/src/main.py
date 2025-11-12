import asyncio
import logging
from bot.bot import GenAIBot
from database.operations import db
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('genai_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    
    try:
        logger.info("🚀 Starting GenAI Insight Bot...")
        
        # Initialize database
        logger.info("📊 Initializing database...")
        db.init_db()
        logger.info("✅ Database initialized successfully")
        
        # Start the bot
        logger.info("🤖 Starting Telegram bot...")
        bot = GenAIBot()
        await bot.start()
        
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())