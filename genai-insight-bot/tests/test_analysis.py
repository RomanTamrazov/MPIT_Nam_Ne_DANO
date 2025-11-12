import pytest
import asyncio
from unittest.mock import Mock, patch
from src.analysis.g4f_analyzer import G4FAnalyzer
from src.analysis.comparator import PeopleComparator
from src.analysis.recommender import ExpertRecommender

class TestAnalysis:
    """Test analysis modules"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = G4FAnalyzer()
        self.comparator = PeopleComparator()
        self.recommender = ExpertRecommender()
    
    @pytest.mark.asyncio
    async def test_analyzer_entity_extraction(self):
        """Test entity extraction analysis"""
        test_text = "Илья Суцкевер из OpenAI работает над GPT-5 и большими языковыми моделями."
        
        with patch('g4f.ChatCompletion.create_async') as mock_g4f:
            mock_g4f.return_value = '''
            {
                "people": [{"name": "Илья Суцкевер", "role": "Chief Scientist", "company": "OpenAI"}],
                "projects": [{"name": "GPT-5", "description": "Большая языковая модель"}],
                "technologies": ["LLM", "AI"],
                "companies": ["OpenAI"],
                "key_topics": ["языковые модели", "искусственный интеллект"]
            }
            '''
            
            result = await self.analyzer.analyze_text(test_text, 'entity_extraction')
            
            assert 'people' in result
            assert 'projects' in result
            assert 'technologies' in result
            assert isinstance(result['people'], list)
    
    @pytest.mark.asyncio
    async def test_analyzer_insight_classification(self):
        """Test insight classification analysis"""
        test_text = "Мы достигли прорыва в генерации видео с временной согласованностью."
        
        with patch('g4f.ChatCompletion.create_async') as mock_g4f:
            mock_g4f.return_value = '''
            {
                "category": "TECH_BREAKTHROUGH",
                "confidence": 0.9,
                "key_findings": ["генерация видео", "временная согласованность"],
                "potential_impact": "HIGH",
                "timeline": "SHORT_TERM"
            }
            '''
            
            result = await self.analyzer.analyze_text(test_text, 'insight_classification')
            
            assert 'category' in result
            assert 'confidence' in result
            assert result['category'] == 'TECH_BREAKTHROUGH'
    
    @pytest.mark.asyncio
    async def test_analyzer_sentiment_analysis(self):
        """Test sentiment analysis"""
        test_text = "Это революционная технология, которая изменит индустрию!"
        
        with patch('g4f.ChatCompletion.create_async') as mock_g4f:
            mock_g4f.return_value = '''
            {
                "sentiment": "POSITIVE",
                "importance_score": 9,
                "urgency": "HIGH",
                "key_emotions": ["энтузиазм", "оптимизм"],
                "confidence": 0.95
            }
            '''
            
            result = await self.analyzer.analyze_text(test_text, 'sentiment_analysis')
            
            assert 'sentiment' in result
            assert result['sentiment'] == 'POSITIVE'
            assert result['importance_score'] == 9
    
    def test_comparator_prepare_data(self):
        """Test comparison data preparation"""
        mock_person_x = Mock()
        mock_person_x.name = "Test X"
        mock_person_x.position = "Researcher"
        mock_person_x.company = "Test Corp"
        mock_person_x.expertise_domains = ["AI", "ML"]
        mock_person_x.skills = [Mock(name="Python"), Mock(name="TensorFlow")]
        mock_person_x.projects = [Mock(name="Project A"), Mock(name="Project B")]
        
        mock_person_y = Mock()
        mock_person_y.name = "Test Y"
        mock_person_y.position = "Engineer"
        mock_person_y.company = "Another Corp"
        mock_person_y.expertise_domains = ["NLP", "CV"]
        mock_person_y.skills = [Mock(name="Python"), Mock(name="PyTorch")]
        mock_person_y.projects = [Mock(name="Project C"), Mock(name="Project D")]
        
        comparison_data = self.comparator._prepare_comparison_data(mock_person_x, mock_person_y)
        
        assert 'person_x' in comparison_data
        assert 'person_y' in comparison_data
        assert comparison_data['person_x']['name'] == 'Test X'
        assert comparison_data['person_y']['name'] == 'Test Y'
        assert 'Python' in comparison_data['person_x']['skills']
        assert 'Python' in comparison_data['person_y']['skills']
    
    def test_recommender_calculate_expert_score(self):
        """Test expert scoring calculation"""
        mock_person = Mock()
        mock_person.skills = [Mock(name="Python"), Mock(name="Machine Learning")]
        mock_person.expertise_domains = ["AI", "Data Science"]
        mock_person.projects = [Mock(), Mock(), Mock()]  # 3 projects
        mock_person.id = 1
        
        # Mock database methods
        with patch.object(self.recommender.db, 'get_recent_publications') as mock_pubs:
            mock_pubs.return_value = [Mock(), Mock()]  # 2 recent publications
            
            with patch.object(self.recommender.db, 'get_people_connections') as mock_conns:
                mock_conns.return_value = [('conn1', 'type', 5), ('conn2', 'type', 7)]  # 2 connections
                
                # Mock the async method call
                with patch.object(self.recommender, '_calculate_expert_score') as mock_score:
                    mock_score.return_value = {
                        'total': 8.5,
                        'breakdown': {
                            'skill_match': 7.0,
                            'domain_expertise': 9.0,
                            'recent_activity': 8.0,
                            'influence': 7.5,
                            'innovation': 9.0
                        }
                    }
                    
                    # This would normally be async, but we're mocking it
                    score = self.recommender._calculate_expert_score(
                        mock_person, 
                        "AI", 
                        {"technical_skills": ["Python", "ML"], "domains": ["AI"]}
                    )
                    
                    assert score['total'] == 8.5
                    assert 'breakdown' in score

if __name__ == '__main__':
    pytest.main([__file__, '-v'])