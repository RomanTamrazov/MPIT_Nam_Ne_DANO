import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import settings
from .handlers import setup_handlers
import asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GenAIBot:
    def __init__(self):
        self.token = settings.BOT_TOKEN
        self.application = Application.builder().token(self.token).build()
        
        # Setup handlers
        setup_handlers(self.application)
    
    async def start(self):
        """Start the bot"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("🤖 GenAI Insight Bot started successfully!")
            
            # Keep the bot running
            await self._keep_alive()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def _keep_alive(self):
        """Keep the bot running"""
        try:
            while True:
                await asyncio.sleep(86400)  # Sleep for 1 day
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """Stop the bot"""
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Bot stopped")

def main():
    """Main function to run the bot"""
    bot = GenAIBot()
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == '__main__':
    main()