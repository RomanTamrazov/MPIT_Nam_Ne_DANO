import g4f
import json
import asyncio
from typing import Dict, List, Any
from config.settings import settings

class G4FAnalyzer:
    def __init__(self):
        self.provider = getattr(g4f.Provider, settings.G4F_PROVIDER.split('.')[-1])
    
    async def analyze_text(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze text using G4F based on analysis type"""
        
        prompts = {
            'entity_extraction': self._entity_extraction_prompt(text),
            'insight_classification': self._insight_classification_prompt(text),
            'sentiment_analysis': self._sentiment_analysis_prompt(text),
            'skill_extraction': self._skill_extraction_prompt(text),
            'trend_detection': self._trend_detection_prompt(text)
        }
        
        prompt = prompts.get(analysis_type, self._default_analysis_prompt(text))
        
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}],
                provider=self.provider
            )
            return self._parse_response(response, analysis_type)
        except Exception as e:
            return {'error': str(e), 'analysis_type': analysis_type}
    
    def _entity_extraction_prompt(self, text: str) -> str:
        return f"""
        Извлеки сущности из текста ниже. Верни В ТОЛЬКО JSON формате:
        
        {{
            "people": [{{"name": "", "role": "", "company": ""}}],
            "projects": [{{"name": "", "description": ""}}],
            "technologies": ["tech1", "tech2"],
            "companies": ["company1", "company2"],
            "key_topics": ["topic1", "topic2"]
        }}
        
        Текст: {text}
        """
    
    def _insight_classification_prompt(self, text: str) -> str:
        return f"""
        Классифицируй текст по следующим категориям. Верни В ТОЛЬКО JSON:
        
        {{
            "category": "TECH_BREAKTHROUGH|NEW_PRODUCT|STRATEGY_CHANGE|RESEARCH_FINDING|MARKET_TREND",
            "confidence": 0.0-1.0,
            "key_findings": ["finding1", "finding2"],
            "potential_impact": "LOW|MEDIUM|HIGH",
            "timeline": "SHORT_TERM|MID_TERM|LONG_TERM"
        }}
        
        Текст: {text}
        """
    
    def _sentiment_analysis_prompt(self, text: str) -> str:
        return f"""
        Проанализируй тон и важность текста. Верни В ТОЛЬКО JSON:
        
        {{
            "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
            "importance_score": 1-10,
            "urgency": "LOW|MEDIUM|HIGH",
            "key_emotions": ["emotion1", "emotion2"],
            "confidence": 0.0-1.0
        }}
        
        Текст: {text}
        """
    
    def _skill_extraction_prompt(self, text: str) -> str:
        return f"""
        Извлеки технические навыки и компетенции из текста. Верни В ТОЛЬКО JSON:
        
        {{
            "technical_skills": ["skill1", "skill2"],
            "domains": ["domain1", "domain2"],
            "experience_level": "JUNIOR|MID|SENIOR|EXPERT",
            "specializations": ["spec1", "spec2"]
        }}
        
        Текст: {text}
        """
    
    def _trend_detection_prompt(self, texts: List[str]) -> str:
        combined_text = "\n".join(texts[:5])  # Analyze first 5 texts
        return f"""
        Выяви emerging тренды из следующих текстов. Верни В ТОЛЬКО JSON:
        
        {{
            "emerging_trends": [
                {{
                    "trend_name": "",
                    "evidence": ["evidence1", "evidence2"],
                    "momentum": 1-10,
                    "key_players": ["player1", "player2"]
                }}
            ],
            "declining_trends": ["trend1", "trend2"],
            "predictions": ["prediction1", "prediction2"]
        }}
        
        Тексты: {combined_text}
        """
    
    def _default_analysis_prompt(self, text: str) -> str:
        return f"""
        Проанализируй текст и верни ключевые инсайты. Верни В ТОЛЬКО JSON:
        
        {{
            "summary": "",
            "key_points": ["point1", "point2"],
            "actionable_insights": ["insight1", "insight2"],
            "follow_up_questions": ["question1", "question2"]
        }}
        
        Текст: {text}
        """
    
    def _parse_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse G4F response into structured JSON"""
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {'raw_response': response, 'analysis_type': analysis_type}
    
    async def batch_analyze(self, texts: List[str], analysis_type: str) -> List[Dict[str, Any]]:
        """Analyze multiple texts concurrently"""
        tasks = [self.analyze_text(text, analysis_type) for text in texts]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Global analyzer instance
analyzer = G4FAnalyzer()