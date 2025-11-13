import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class GraphVisualizer:
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'accent': '#2ca02c',
            'background': '#f8f9fa'
        }
    
    def create_people_comparison_chart(self, person_x_data: Dict, person_y_data: Dict, scores: Dict) -> str:
        """Создает сравнительную диаграмму двух экспертов"""
        try:
            categories = ['Навыки', 'Опыт', 'Проекты', 'Публикации', 'Влияние']
            person_x_scores = [
                scores.get('skills_score_x', 0),
                scores.get('experience_score_x', 0), 
                scores.get('projects_score_x', 0),
                scores.get('publications_score_x', 0),
                scores.get('influence_score_x', 0)
            ]
            person_y_scores = [
                scores.get('skills_score_y', 0),
                scores.get('experience_score_y', 0),
                scores.get('projects_score_y', 0), 
                scores.get('publications_score_y', 0),
                scores.get('influence_score_y', 0)
            ]

            fig = go.Figure()

            fig.add_trace(go.Scatterpolar(
                r=person_x_scores,
                theta=categories,
                fill='toself',
                name=person_x_data.get('name', 'Эксперт X'),
                line_color=self.colors['primary']
            ))

            fig.add_trace(go.Scatterpolar(
                r=person_y_scores,
                theta=categories,
                fill='toself', 
                name=person_y_data.get('name', 'Эксперт Y'),
                line_color=self.colors['secondary']
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10]
                    )),
                showlegend=True,
                title=f"Сравнение: {person_x_data.get('name', 'X')} vs {person_y_data.get('name', 'Y')}",
                template="plotly_white"
            )

            return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})
            
        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            return "<div>Ошибка при создании диаграммы сравнения</div>"
    
    def create_network_graph(self, people_data: List[Dict], connections: List[tuple]) -> str:
        """Создает граф связей между экспертами"""
        try:
            if not people_data:
                return "<div>Нет данных для построения графа</div>"

            # Создаем узлы
            node_x = []
            node_y = []
            node_text = []
            node_size = []
            node_color = []
            node_names = []

            for i, person in enumerate(people_data):
                # Распределяем узлы по кругу для лучшего отображения
                angle = 2 * 3.14159 * i / len(people_data)
                radius = 10 + (len(person.get('skills', [])) / 5)  # Больше навыков - дальше от центра
                node_x.append(radius * np.cos(angle))
                node_y.append(radius * np.sin(angle))
                
                # Формируем текст для узла
                skills_text = ', '.join(person.get('skills', [])[:3])
                if len(person.get('skills', [])) > 3:
                    skills_text += f"... (+{len(person.get('skills', [])) - 3})"
                    
                node_text.append(
                    f"<b>{person.get('name', 'Unknown')}</b><br>"
                    f"Компания: {person.get('company', 'Не указана')}<br>"
                    f"Должность: {person.get('position', 'Не указана')}<br>"
                    f"Навыки: {skills_text}"
                )
                
                # Размер узла зависит от количества навыков
                node_size.append(20 + len(person.get('skills', [])) * 3)
                node_color.append(len(person.get('skills', [])))  # Цвет по количеству навыков
                node_names.append(person.get('name', 'Unknown'))

            # Создаем ребра
            edge_x = []
            edge_y = []
            edge_text = []

            for connection in connections:
                idx1, idx2 = connection
                x0, y0 = node_x[idx1], node_y[idx1]
                x1, y1 = node_x[idx2], node_y[idx2]
                
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
                # Находим общие навыки для подписи связи
                skills1 = set(people_data[idx1].get('skills', []))
                skills2 = set(people_data[idx2].get('skills', []))
                common_skills = skills1 & skills2
                
                if common_skills:
                    edge_text.append(f"Общие навыки: {', '.join(list(common_skills)[:2])}")
                else:
                    edge_text.append("Одна компания")

            # Создаем граф
            fig = go.Figure()

            # Добавляем ребра
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color='#888', dash='dot'),
                hoverinfo='text',
                text=edge_text * 3,  # Повторяем для каждой точки линии
                mode='lines',
                showlegend=False,
                name='Связи'
            ))

            # Добавляем узлы
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                hovertext=node_text,
                text=node_names,
                textposition="middle center",
                marker=dict(
                    size=node_size,
                    color=node_color,
                    colorscale='Viridis',
                    line=dict(width=3, color='white'),
                    showscale=True,
                    colorbar=dict(title="Кол-во навыков")
                ),
                name='Эксперты'
            ))

            fig.update_layout(
                title="🔗 Сеть экспертов - связи по общим навыкам и компаниям",
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[dict(
                    text="💡 Размер узла = количество навыков<br>Цвет = интенсивность навыков",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1
                )],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                template="plotly_white",
                height=600
            )

            return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': True})
            
        except Exception as e:
            logger.error(f"Error creating network graph: {e}")
            return f"<div>Ошибка при создании графа связей: {str(e)}</div>"
    
    def create_recommendations_chart(self, recommendations: List[Dict]) -> str:
        """Создает диаграмму рекомендаций экспертов"""
        try:
            if not recommendations:
                return "<div>Нет рекомендаций для визуализации</div>"

            # Подготавливаем данные
            names = [rec.get('name', 'Unknown') for rec in recommendations]
            scores = [rec.get('score', 0) for rec in recommendations]
            companies = [rec.get('company', 'Не указана') for rec in recommendations]

            # Создаем столбчатую диаграмму
            fig = px.bar(
                x=names,
                y=scores,
                color=companies,
                title="Рекомендации экспертов по релевантности",
                labels={'x': 'Эксперты', 'y': 'Баллы релевантности'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig.update_layout(
                xaxis_tickangle=-45,
                template="plotly_white",
                showlegend=True
            )

            return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})
            
        except Exception as e:
            logger.error(f"Error creating recommendations chart: {e}")
            return "<div>Ошибка при создании диаграммы рекомендаций</div>"

    def create_skills_heatmap(self, people_data: List[Dict]) -> str:
        """Создает тепловую карту навыков экспертов"""
        try:
            if not people_data:
                return "<div>Нет данных для тепловой карты</div>"

            # Собираем все уникальные навыки
            all_skills = set()
            for person in people_data:
                all_skills.update(person.get('skills', []))
            
            all_skills = sorted(list(all_skills))[:15]  # Ограничиваем для читаемости

            # Создаем матрицу присутствия навыков
            matrix = []
            names = []
            
            for person in people_data[:10]:  # Ограничиваем количество экспертов
                names.append(person.get('name', 'Unknown'))
                row = [1 if skill in person.get('skills', []) else 0 for skill in all_skills]
                matrix.append(row)

            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=all_skills,
                y=names,
                colorscale='Blues',
                hoverongaps=False,
                showscale=False
            ))

            fig.update_layout(
                title="Навыки экспертов",
                xaxis_title="Навыки",
                yaxis_title="Эксперты",
                template="plotly_white"
            )

            return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})
            
        except Exception as e:
            logger.error(f"Error creating skills heatmap: {e}")
            return "<div>Ошибка при создании тепловой карты</div>"

    def create_company_distribution(self, people_data: List[Dict]) -> str:
        """Создает диаграмму распределения экспертов по компаниям"""
        try:
            if not people_data:
                return "<div>Нет данных для диаграммы компаний</div>"

            # Собираем статистику по компаниям
            companies = {}
            for person in people_data:
                company = person.get('company', 'Не указана')
                companies[company] = companies.get(company, 0) + 1

            # Берем топ-10 компаний
            top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
            company_names = [c[0] for c in top_companies]
            company_counts = [c[1] for c in top_companies]

            fig = px.pie(
                values=company_counts,
                names=company_names,
                title="Распределение экспертов по компаниям",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(template="plotly_white")

            return fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': False})
            
        except Exception as e:
            logger.error(f"Error creating company distribution: {e}")
            return "<div>Ошибка при создании диаграммы компаний</div>"

# Импортируем numpy для математических операций
import numpy as np

visualizer = GraphVisualizer()