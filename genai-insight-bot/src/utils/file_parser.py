import pandas as pd
import json
import logging
from typing import Dict, List, Any
import io
from database.operations import db

logger = logging.getLogger(__name__)

class FileParser:
    def __init__(self):
        self.field_mapping = {
            'name': ['name', 'имя', 'fullname', 'full_name', 'person', 'фио'],
            'position': ['position', 'должность', 'title', 'role', 'job_title', 'профессия'],
            'company': ['company', 'компания', 'organization', 'org', 'employer', 'workplace', 'организация'],
            'skills': ['skills', 'skill', 'навыки', 'competencies', 'expertise', 'технологии'],
            'projects': ['projects', 'project', 'проекты', 'works', 'achievements', 'достижения'],
            'publications': ['publications', 'publication', 'публикации', 'papers', 'articles', 'статьи'],
            'twitter': ['twitter', 'tw', 'твиттер'],
            'linkedin': ['linkedin', 'ln', 'линкедин'],
            'github': ['github', 'gh', 'гитхаб']
        }
    
    def _normalize_column_name(self, column: str) -> str:
        """Нормализует название столбца для сопоставления"""
        column = str(column).lower().strip()
        
        for standard_field, synonyms in self.field_mapping.items():
            if column in synonyms:
                return standard_field
        
        return column
    
    async def parse_file(self, file_content: bytes, filename: str, telegram_id: str) -> Dict[str, Any]:
        """Универсальный парсер файлов для конкретного пользователя"""
        file_extension = filename.lower().split('.')[-1]
        
        try:
            if file_extension in ['csv', 'tsv']:
                return await self._parse_delimited(file_content, filename, telegram_id)
            elif file_extension in ['xlsx', 'xls']:
                return await self._parse_excel(file_content, filename, telegram_id)
            elif file_extension == 'json':
                return await self._parse_json(file_content, filename, telegram_id)
            else:
                return {'error': f'Неподдерживаемый формат: {file_extension}'}
                
        except Exception as e:
            logger.error(f"Error parsing file {filename} for user {telegram_id}: {e}")
            return {'error': f'Ошибка парсинга: {str(e)}'}
    
    async def _parse_delimited(self, file_content: bytes, filename: str, telegram_id: str) -> Dict[str, Any]:
        """Парсит CSV/TSV файлы"""
        delimiter = ',' if filename.lower().endswith('.csv') else '\t'
        
        for encoding in ['utf-8', 'windows-1251', 'cp1251']:
            try:
                df = pd.read_csv(io.BytesIO(file_content), delimiter=delimiter, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return {'error': 'Не удалось определить кодировку файла'}
        
        return await self._process_dataframe(df, filename, telegram_id)
    
    async def _parse_excel(self, file_content: bytes, filename: str, telegram_id: str) -> Dict[str, Any]:
        """Парсит Excel файлы"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            return await self._process_dataframe(df, filename, telegram_id)
        except Exception as e:
            return {'error': f'Ошибка чтения Excel: {str(e)}'}
    
    async def _parse_json(self, file_content: bytes, filename: str, telegram_id: str) -> Dict[str, Any]:
        """Парсит JSON файлы"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'experts' in data:
                df = pd.DataFrame(data['experts'])
            elif isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame([data])
            
            return await self._process_dataframe(df, filename, telegram_id)
            
        except Exception as e:
            return {'error': f'Ошибка парсинга JSON: {str(e)}'}
    
    async def _process_dataframe(self, df: pd.DataFrame, filename: str, telegram_id: str) -> Dict[str, Any]:
        """Обрабатывает DataFrame с автоматическим определением структуры"""
        try:
            # Нормализуем названия столбцов
            df.columns = [self._normalize_column_name(col) for col in df.columns]
            
            # Анализ структуры данных
            structure_analysis = self._analyze_structure(df)
            
            # Обрабатываем данные
            experts_added = 0
            publications_added = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    person_data = self._extract_person_data(row)
                    
                    if not person_data.get('name'):
                        errors.append(f"Строка {index+1}: отсутствует имя")
                        continue
                    
                    # Сохраняем в базу для конкретного пользователя
                    person_id = db.add_person(
                        telegram_id=telegram_id,
                        name=person_data['name'],
                        position=person_data.get('position', ''),
                        company=person_data.get('company', ''),
                        skills=person_data.get('skills', []),
                        projects=person_data.get('projects', []),
                        social_links=person_data.get('social_links', {})
                    )
                    
                    if person_id:
                        experts_added += 1
                        
                        # Обрабатываем публикации если есть
                        if 'publications' in person_data and person_data['publications']:
                            publications = self._parse_publications(person_data['publications'])
                            for pub in publications:
                                db.add_publication(
                                    telegram_id=telegram_id,
                                    expert_name=person_data['name'],
                                    content=pub.get('title', ''),
                                    source=pub.get('type', 'unknown')
                                )
                                publications_added += 1
                    
                except Exception as e:
                    errors.append(f"Строка {index+1}: {str(e)}")
            
            # Генерируем анализ данных
            analysis = await self._generate_analysis(df, experts_added)
            
            return {
                'experts_added': experts_added,
                'publications_added': publications_added,
                'analysis': analysis,
                'structure_analysis': structure_analysis,
                'errors': errors,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Error processing dataframe for user {telegram_id}: {e}")
            return {'error': f'Ошибка обработки данных: {str(e)}'}
    
    def _analyze_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Анализирует структуру данных"""
        detected_fields = {}
        missing_required = []
        
        required_fields = ['name', 'position', 'company']
        
        for field in required_fields:
            if field in df.columns:
                non_empty = df[field].notna().sum()
                detected_fields[field] = {
                    'detected': True,
                    'non_empty_count': non_empty,
                    'completeness': f"{(non_empty/len(df))*100:.1f}%"
                }
            else:
                detected_fields[field] = {'detected': False}
                missing_required.append(field)
        
        optional_fields = ['skills', 'projects', 'publications', 'twitter', 'linkedin', 'github']
        for field in optional_fields:
            if field in df.columns:
                non_empty = df[field].notna().sum()
                detected_fields[field] = {
                    'detected': True,
                    'non_empty_count': non_empty,
                    'completeness': f"{(non_empty/len(df))*100:.1f}%"
                }
            else:
                detected_fields[field] = {'detected': False}
        
        return {
            'total_rows': len(df),
            'detected_fields': detected_fields,
            'missing_required': missing_required,
            'data_quality': f"{(len([f for f in required_fields if f in df.columns])/len(required_fields))*100:.1f}%"
        }
    
    def _extract_person_data(self, row) -> Dict[str, Any]:
        """Извлекает данные человека из строки"""
        data = {}
        
        for field in ['name', 'position', 'company', 'twitter', 'linkedin', 'github']:
            if field in row and pd.notna(row[field]):
                data[field] = str(row[field]).strip()
        
        for field in ['skills', 'projects', 'publications']:
            if field in row and pd.notna(row[field]):
                data[field] = self._parse_list_field(row[field])
        
        # Собираем социальные ссылки
        social_links = {}
        for field in ['twitter', 'linkedin', 'github']:
            if field in data:
                social_links[field] = data[field]
                del data[field]
        
        if social_links:
            data['social_links'] = social_links
        
        return data
    
    def _parse_list_field(self, value) -> List[str]:
        """Парсит поля со списками значений"""
        if isinstance(value, list):
            return [str(item).strip() for item in value]
        elif isinstance(value, str):
            separators = [',', ';', '|', '\n']
            for sep in separators:
                if sep in value:
                    return [item.strip() for item in value.split(sep) if item.strip()]
            return [value.strip()]
        return []
    
    def _parse_publications(self, publications_data) -> List[Dict[str, str]]:
        """Парсит публикации"""
        publications = []
        
        if isinstance(publications_data, list):
            for pub in publications_data:
                if isinstance(pub, str):
                    publications.append({'title': pub, 'type': 'unknown'})
                elif isinstance(pub, dict):
                    publications.append(pub)
        
        return publications
    
    async def _generate_analysis(self, df: pd.DataFrame, experts_added: int) -> Dict[str, Any]:
        """Генерирует анализ данных"""
        analysis = {
            'stats': {},
            'insights': [],
            'top_companies': {},
            'top_skills': {},
            'warnings': []
        }
        
        try:
            analysis['stats'] = {
                'total_experts': experts_added,
                'total_rows': len(df),
                'success_rate': f"{(experts_added/len(df))*100:.1f}%" if len(df) > 0 else "0%"
            }
            
            if 'company' in df.columns:
                companies_analysis = df['company'].value_counts()
                analysis['top_companies'] = companies_analysis.head(10).to_dict()
                
                if len(companies_analysis) > 0:
                    top_company = companies_analysis.index[0]
                    analysis['insights'].append(f"Наибольшее количество экспертов из {top_company}")
            
            if 'skills' in df.columns:
                all_skills = []
                for skills in df['skills'].dropna():
                    if isinstance(skills, list):
                        all_skills.extend(skills)
                    elif isinstance(skills, str):
                        all_skills.extend(self._parse_list_field(skills))
                
                from collections import Counter
                skills_count = Counter(all_skills)
                analysis['top_skills'] = dict(skills_count.most_common(10))
                
                if analysis['top_skills']:
                    top_skill = list(analysis['top_skills'].keys())[0]
                    analysis['insights'].append(f"Самый популярный навык: {top_skill}")
            
            missing_name = df['name'].isna().sum() if 'name' in df.columns else len(df)
            if missing_name > 0:
                analysis['warnings'].append(f"Обнаружено {missing_name} записей без имени")
            
            if experts_added < len(df):
                analysis['warnings'].append(f"Обработано {experts_added} из {len(df)} записей")
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            analysis['warnings'].append("Ошибка при анализе данных")
        
        return analysis

# Создаем экземпляр парсера
file_parser = FileParser()