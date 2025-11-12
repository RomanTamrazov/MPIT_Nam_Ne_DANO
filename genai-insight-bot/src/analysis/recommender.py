from database.operations import db
import logging

logger = logging.getLogger(__name__)

class ExpertRecommender:
    def __init__(self):
        self.db = db
    
    async def recommend_experts(self, topic: str, max_recommendations: int = 5):
        all_people = self.db.get_all_people()
        return {
            'topic': topic,
            'recommendations': [p.name for p in all_people[:max_recommendations]]
        }
    
    async def get_recommendation_report(self, topic: str, max_recommendations: int = 5) -> str:
        result = await self.recommend_experts(topic, max_recommendations)
        
        return f"""
🔍 Рекомендации по теме: {topic}

📊 Найдено экспертов: {len(result['recommendations'])}

💡 Бот работает успешно!
"""

recommender = ExpertRecommender()