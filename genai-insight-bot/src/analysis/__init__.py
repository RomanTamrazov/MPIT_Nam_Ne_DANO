from .g4f_analyzer import G4FAnalyzer, analyzer

# Заглушки для остальных модулей
class PeopleComparator:
    async def compare_people(self, x, y):
        return f"Comparison: {x} vs {y}"
    
    async def generate_comparison_report(self, x, y):
        return f"Report: {x} vs {y}"

class ExpertRecommender:
    async def recommend_experts(self, topic):
        return {'recommendations': []}
    
    async def get_recommendation_report(self, topic):
        return f"Recommendations for: {topic}"

comparator = PeopleComparator()
recommender = ExpertRecommender()

__all__ = [
    'G4FAnalyzer', 'analyzer',
    'PeopleComparator', 'comparator', 
    'ExpertRecommender', 'recommender'
]