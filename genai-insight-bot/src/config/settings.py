import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database (Supabase)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # G4F Configuration
    G4F_PROVIDER = os.getenv('G4F_PROVIDER', 'g4f.Provider.Bing')
    
    # Analysis Settings
    MAX_RECOMMENDATIONS = 5
    COMPARISON_METRICS = ['expertise', 'influence', 'innovation', 'activity']
    
    # File Processing
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.csv', '.json', '.txt', '.pdf'}

settings = Settings()