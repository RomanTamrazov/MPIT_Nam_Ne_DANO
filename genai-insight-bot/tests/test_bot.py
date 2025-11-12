import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Update, Message, Chat, User
from src.bot.handlers import *

class TestBotHandlers:
    """Test bot handlers"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.update = Mock(spec=Update)
        self.context = Mock()
        self.message = Mock(spec=Message)
        self.chat = Mock(spec=Chat)
        self.user = Mock(spec=User)
        
        self.message.chat = self.chat
        self.update.message = self.message
        self.context.args = []
    
    @pytest.mark.asyncio
    async def test_start_command(self):
        """Test start command handler"""
        self.message.reply_text = AsyncMock()
        
        await start_command(self.update, self.context)
        
        # Check that reply_text was called
        self.message.reply_text.assert_called_once()
        call_args = self.message.reply_text.call_args[0][0]
        assert "Добро пожаловать" in call_args
    
    @pytest.mark.asyncio
    async def test_compare_command_no_args(self):
        """Test compare command without arguments"""
        self.message.reply_text = AsyncMock()
        self.context.args = []
        
        await compare_command(self.update, self.context)
        
        self.message.reply_text.assert_called_once()
        call_args = self.message.reply_text.call_args[0][0]
        assert "Используйте" in call_args
    
    @pytest.mark.asyncio
    async def test_compare_command_invalid_format(self):
        """Test compare command with invalid format"""
        self.message.reply_text = AsyncMock()
        self.context.args = ["Ilya", "Sutskever"]  # No "vs"
        
        await compare_command(self.update, self.context)
        
        self.message.reply_text.assert_called_once()
        call_args = self.message.reply_text.call_args[0][0]
        assert "используйте 'vs'" in call_args
    
    @pytest.mark.asyncio
    async def test_recommend_command_no_args(self):
        """Test recommend command without arguments"""
        self.message.reply_text = AsyncMock()
        self.context.args = []
        
        await recommend_command(self.update, self.context)
        
        self.message.reply_text.assert_called_once()
        call_args = self.message.reply_text.call_args[0][0]
        assert "Укажите тему" in call_args
    
    @pytest.mark.asyncio
    async def test_stats_command(self):
        """Test stats command"""
        self.message.reply_text = AsyncMock()
        
        await stats_command(self.update, self.context)
        
        self.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_people_command_no_args(self):
        """Test people command without arguments"""
        self.message.reply_text = AsyncMock()
        self.context.args = []
        
        await people_command(self.update, self.context)
        
        self.message.reply_text.assert_called_once()
        call_args = self.message.reply_text.call_args[0][0]
        assert "Укажите имя" in call_args

if __name__ == '__main__':
    pytest.main([__file__, '-v'])