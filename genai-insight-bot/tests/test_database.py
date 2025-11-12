import pytest
import asyncio
from src.database.operations import DatabaseManager
from src.database.models import Person, Publication
from src.config.settings import settings

class TestDatabase:
    """Test database operations"""
    
    def setup_method(self):
        """Setup test database"""
        self.db = DatabaseManager()
        # Use test database
        self.db.engine = create_engine('sqlite:///:memory:')
        self.db.init_db()
    
    def test_add_person(self):
        """Test adding a person to database"""
        person_data = {
            'name': 'Test Person',
            'position': 'AI Researcher',
            'company': 'Test Corp'
        }
        
        person = self.db.add_person(person_data)
        
        assert person.id is not None
        assert person.name == 'Test Person'
        assert person.position == 'AI Researcher'
    
    def test_get_person_by_name(self):
        """Test retrieving person by name"""
        person_data = {
            'name': 'Test Researcher',
            'position': 'Researcher',
            'company': 'AI Lab'
        }
        
        self.db.add_person(person_data)
        found_person = self.db.get_person_by_name('Test Researcher')
        
        assert found_person is not None
        assert found_person.name == 'Test Researcher'
    
    def test_search_people_by_skill(self):
        """Test searching people by skill"""
        # This would require setting up skills relationships
        # For now, test the method exists
        result = self.db.search_people_by_skill('Python')
        assert isinstance(result, list)
    
    def test_add_publication(self):
        """Test adding a publication"""
        # First create a person
        person = self.db.add_person({
            'name': 'Test Author',
            'position': 'Author',
            'company': 'Test'
        })
        
        publication_data = {
            'person_id': person.id,
            'content': 'Test publication content',
            'source': 'twitter',
            'g4f_analysis': {'key': 'value'}
        }
        
        publication = self.db.add_publication(publication_data)
        
        assert publication.id is not None
        assert publication.content == 'Test publication content'
    
    def test_get_recent_publications(self):
        """Test retrieving recent publications"""
        publications = self.db.get_recent_publications(limit=5)
        assert isinstance(publications, list)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])