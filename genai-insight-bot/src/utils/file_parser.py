import pandas as pd
import json
import csv
from typing import Dict, List, Any
import io
from database.operations import db
from analysis.g4f_analyzer import analyzer

class FileParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.json', '.txt']
    
    async def parse_file(self, file_content: bytes, filename: str, file_type: str) -> Dict[str, Any]:
        """Parse uploaded file and extract structured data"""
        
        try:
            if file_type == 'csv':
                return await self._parse_csv(file_content, filename)
            elif file_type == 'json':
                return await self._parse_json(file_content, filename)
            elif file_type == 'txt':
                return await self._parse_txt(file_content, filename)
            else:
                return {'error': f'Unsupported file format: {file_type}'}
        except Exception as e:
            return {'error': f'File parsing error: {str(e)}'}
    
    async def _parse_csv(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse CSV file with people data"""
        
        df = pd.read_csv(io.BytesIO(content))
        results = {
            'people_processed': 0,
            'projects_processed': 0,
            'publications_processed': 0,
            'errors': []
        }
        
        for _, row in df.iterrows():
            try:
                # Process person data
                person_data = {
                    'name': row.get('name', ''),
                    'position': row.get('position', ''),
                    'company': row.get('company', ''),
                    'social_links': self._parse_social_links(row)
                }
                
                person = db.add_person(person_data)
                results['people_processed'] += 1
                
                # Process projects if available
                if 'projects' in row and pd.notna(row['projects']):
                    projects = self._parse_projects(row['projects'], person.id)
                    results['projects_processed'] += len(projects)
                
                # Process publications if available
                if 'publications' in row and pd.notna(row['publications']):
                    publications = await self._parse_publications(row['publications'], person.id)
                    results['publications_processed'] += len(publications)
                    
            except Exception as e:
                results['errors'].append(f"Error processing row {_}: {str(e)}")
        
        return results
    
    async def _parse_json(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse JSON file with structured data"""
        
        data = json.loads(content.decode('utf-8'))
        results = {
            'people_processed': 0,
            'analysis_performed': 0,
            'insights_found': 0
        }
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Assume it's a list of people
            for person_data in data:
                try:
                    db.add_person(person_data)
                    results['people_processed'] += 1
                except Exception as e:
                    continue
        
        elif isinstance(data, dict):
            # Assume it's a structured dataset
            if 'people' in data:
                for person_data in data['people']:
                    db.add_person(person_data)
                    results['people_processed'] += 1
            
            # Analyze content with G4F if it contains text
            if 'content' in data:
                analysis = await analyzer.analyze_text(str(data['content']), 'entity_extraction')
                results['analysis_performed'] += 1
                results['insights_found'] = len(analysis.get('people', []))
        
        return results
    
    async def _parse_txt(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse text file and extract insights"""
        
        text = content.decode('utf-8')
        results = {
            'analysis_performed': 1,
            'entities_found': 0,
            'insights_extracted': 0
        }
        
        # Analyze text with G4F
        analysis = await analyzer.analyze_text(text, 'entity_extraction')
        
        # Process extracted entities
        if 'people' in analysis:
            for person_data in analysis['people']:
                try:
                    db.add_person(person_data)
                    results['entities_found'] += 1
                except:
                    continue
        
        if 'key_topics' in analysis:
            results['insights_extracted'] = len(analysis['key_topics'])
        
        results['raw_analysis'] = analysis
        
        return results
    
    def _parse_social_links(self, row) -> Dict[str, str]:
        """Parse social links from row data"""
        
        links = {}
        social_platforms = ['twitter', 'linkedin', 'github', 'medium', 'arxiv']
        
        for platform in social_platforms:
            if platform in row and pd.notna(row[platform]):
                links[platform] = row[platform]
        
        return links
    
    def _parse_projects(self, projects_str: str, person_id: int) -> List[Dict]:
        """Parse projects string into structured data"""
        
        projects = []
        if isinstance(projects_str, str):
            project_list = [p.strip() for p in projects_str.split(';') if p.strip()]
            
            for project_name in project_list:
                project_data = {
                    'name': project_name,
                    'person_id': person_id
                }
                # db.add_project(project_data)  # Implement this in operations.py
                projects.append(project_data)
        
        return projects
    
    async def _parse_publications(self, publications_str: str, person_id: int) -> List[Dict]:
        """Parse publications and analyze with G4F"""
        
        publications = []
        if isinstance(publications_str, str):
            pub_list = [p.strip() for p in publications_str.split(';') if p.strip()]
            
            for pub_content in pub_list:
                # Analyze publication with G4F
                analysis = await analyzer.analyze_text(pub_content, 'insight_classification')
                
                publication_data = {
                    'person_id': person_id,
                    'content': pub_content,
                    'source': 'uploaded_file',
                    'g4f_analysis': analysis
                }
                
                db.add_publication(publication_data)
                publications.append(publication_data)
        
        return publications
    
    def get_supported_formats(self) -> List[str]:
        return self.supported_formats

# Global parser instance
file_parser = FileParser()