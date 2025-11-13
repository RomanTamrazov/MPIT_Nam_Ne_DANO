import asyncio
import logging
from bot.bot import GenAIBot
from database.operations import db
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("🚀 Запуск GenAI Insight Bot...")
        
        # Инициализация базы данных
        logger.info("📊 Инициализация базы данных...")
        db.init_db()
        logger.info("✅ База данных готова")
        
        # Запуск бота
        logger.info("🤖 Запуск Telegram бота...")
        bot = GenAIBot()
        await bot.start()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())