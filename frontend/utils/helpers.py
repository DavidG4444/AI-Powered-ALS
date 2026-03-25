import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

def check_authentication():
    """Check if user is authenticated"""
    if not st.session_state.get('logged_in', False):
        st.warning("⚠️ Please login first!")
        st.stop()

def logout():
    """Logout user"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.token = None
    st.session_state.current_question = None
    st.rerun()

def format_time(seconds: int) -> str:
    """Format seconds to readable time"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_mastery_color(mastery: float) -> str:
    """Get color based on mastery level"""
    if mastery >= 0.8:
        return "#10b981"  # Green
    elif mastery >= 0.6:
        return "#3b82f6"  # Blue
    elif mastery >= 0.4:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red

def get_mastery_emoji(mastery: float) -> str:
    """Get emoji based on mastery level"""
    if mastery >= 0.8:
        return "🌟"
    elif mastery >= 0.6:
        return "📈"
    elif mastery >= 0.4:
        return "📊"
    else:
        return "⚠️"

def plot_mastery_gauge(mastery: float, title: str = "Mastery Level"):
    """Create gauge chart for mastery"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=mastery * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': 60, 'increasing': {'color': "#10b981"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': get_mastery_color(mastery)},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#fecaca'},
                {'range': [40, 60], 'color': '#fed7aa'},
                {'range': [60, 80], 'color': '#bfdbfe'},
                {'range': [80, 100], 'color': '#d1fae5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return fig

def plot_progress_line(progress_data):
    """Create line chart for progress over time"""
    if not progress_data:
        return None

    dates = [d['date'] for d in progress_data]
    accuracy = [d['accuracy'] for d in progress_data]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=accuracy,
        mode='lines+markers',
        name='Accuracy',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))

    # Add target line
    fig.add_hline(y=70, line_dash="dash", line_color="green",
                  annotation_text="Target: 70%")

    fig.update_layout(
        title="Performance Over Time",
        xaxis_title="Date",
        yaxis_title="Accuracy (%)",
        hovermode='x unified',
        height=400,
        yaxis=dict(range=[0, 100])
    )

    return fig

def plot_topic_performance(topic_data):
    """Create bar chart for topic performance"""
    if not topic_data:
        return None

    topics = [t['topic'] for t in topic_data]
    mastery = [t['mastery_level'] * 100 for t in topic_data]
    colors = [get_mastery_color(t['mastery_level']) for t in topic_data]

    fig = go.Figure(data=[
        go.Bar(
            x=topics,
            y=mastery,
            marker_color=colors,
            text=[f"{m:.1f}%" for m in mastery],
            textposition='auto',
        )
    ])

    fig.update_layout(
        title="Mastery by Topic",
        xaxis_title="Topic",
        yaxis_title="Mastery (%)",
        height=400,
        yaxis=dict(range=[0, 100]),
        showlegend=False
    )

    return fig

def display_metrics_row(metrics: dict):
    """Display metrics in columns"""
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics.items()):
        with col:
            if delta:
                st.metric(label, value, delta)
            else:
                st.metric(label, value)
