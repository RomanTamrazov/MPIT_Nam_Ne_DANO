import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database - теперь только SQLite
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./genai_experts.db')
    
    # G4F Configuration
    G4F_PROVIDER = os.getenv('G4F_PROVIDER', 'g4f.Provider.Bing')
    
    # App Settings
    MAX_RECOMMENDATIONS = 5

settings = Settings()