import pandas as pd
import json
from database.operations import db

class FileParser:
    
    async def parse_csv(self, file_content, filename):
        """Простой парсер CSV"""
        try:
            df = pd.read_csv(file_content)
            results = {'experts_added': 0, 'errors': []}
            
            for index, row in df.iterrows():
                try:
                    expert_data = {
                        'name': row.get('name', '').strip(),
                        'position': row.get('position', '').strip(),
                        'company': row.get('company', '').strip(),
                        'skills': self._parse_list_field(row.get('skills', '')),
                        'projects': self._parse_list_field(row.get('projects', '')),
                        'social_links': {
                            'twitter': row.get('twitter', '').strip(),
                            'linkedin': row.get('linkedin', '').strip()
                        }
                    }
                    
                    db.add_person(**expert_data)
                    results['experts_added'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Row {index}: {str(e)}")
            
            return results
            
        except Exception as e:
            return {'error': f'CSV error: {str(e)}'}
    
    def _parse_list_field(self, field_value):
        if pd.isna(field_value) or not field_value:
            return []
        items = [item.strip() for item in str(field_value).split(',')]
        return [item for item in items if item]

file_parser = FileParser()