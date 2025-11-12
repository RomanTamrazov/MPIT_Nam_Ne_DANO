import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Any
from database.operations import db

class GraphVisualizer:
    def __init__(self):
        self.db = db
    
    def create_people_comparison_chart(self, person_x_data: Dict, person_y_data: Dict, scores: Dict) -> str:
        """Create radar chart for people comparison"""
        
        categories = ['Техническая экспертиза', 'Влияние', 'Инновационность', 
                     'Активность', 'Сетевое влияние']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[scores['person_x']['technical'], scores['person_x']['influence'],
               scores['person_x']['innovation'], scores['person_x']['activity'],
               scores['person_x']['network']],
            theta=categories,
            fill='toself',
            name=person_x_data['name']
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[scores['person_y']['technical'], scores['person_y']['influence'],
               scores['person_y']['innovation'], scores['person_y']['activity'],
               scores['person_y']['network']],
            theta=categories,
            fill='toself',
            name=person_y_data['name']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title=f"Сравнение: {person_x_data['name']} vs {person_y_data['name']}"
        )
        
        return self._fig_to_html(fig)
    
    def create_network_graph(self, person_id: int, depth: int = 2) -> str:
        """Create network graph visualization for a person"""
        
        G = nx.Graph()
        
        # Add central person
        person = self.db.get_person_by_id(person_id)
        G.add_node(person.id, label=person.name, type='central', size=20)
        
        # Add direct connections
        connections = self.db.get_people_connections(person_id)
        for conn_name, conn_type, strength in connections:
            G.add_node(conn_name, label=conn_name, type='connection', size=15)
            G.add_edge(person.name, conn_name, weight=strength, label=conn_type)
        
        # Create plot
        pos = nx.spring_layout(G)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=[person.name],
                              node_color='red',
                              node_size=1000,
                              alpha=0.7)
        
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=[n for n in G.nodes() if n != person.name],
                              node_color='lightblue',
                              node_size=700,
                              alpha=0.7)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        plt.title(f"Сеть связей: {person.name}")
        plt.axis('off')
        
        return self._plt_to_base64(fig)
    
    def create_recommendations_chart(self, recommendations: List[Dict]) -> str:
        """Create bar chart for expert recommendations"""
        
        names = [rec['name'] for rec in recommendations]
        scores = [rec['relevance_score'] for rec in recommendations]
        
        fig = go.Figure(data=[
            go.Bar(x=names, y=scores,
                  marker_color=['gold' if i == 0 else 'silver' if i == 1 else 'brown' if i == 2 else 'lightblue' 
                               for i in range(len(names))])
        ])
        
        fig.update_layout(
            title='Рейтинг рекомендованных экспертов',
            xaxis_title='Эксперты',
            yaxis_title='Релевантность',
            yaxis=dict(range=[0, 10])
        )
        
        return self._fig_to_html(fig)
    
    def create_skill_comparison_chart(self, person_x_skills: List, person_y_skills: List) -> str:
        """Create skill comparison chart"""
        
        all_skills = list(set(person_x_skills + person_y_skills))
        x_presence = [1 if skill in person_x_skills else 0 for skill in all_skills]
        y_presence = [1 if skill in person_y_skills else 0 for skill in all_skills]
        
        fig = go.Figure(data=[
            go.Bar(name='Person X', x=all_skills, y=x_presence),
            go.Bar(name='Person Y', x=all_skills, y=y_presence)
        ])
        
        fig.update_layout(
            title='Сравнение навыков',
            xaxis_title='Навыки',
            yaxis_title='Наличие',
            barmode='group'
        )
        
        return self._fig_to_html(fig)
    
    def _fig_to_html(self, fig) -> str:
        """Convert plotly figure to HTML string"""
        return fig.to_html(include_plotlyjs='cdn')
    
    def _plt_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str

# Global visualizer instance
visualizer = GraphVisualizer()