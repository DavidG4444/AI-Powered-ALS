import streamlit as st
from utils.api_client import get_api_client
from utils.helpers import (
    init_session_state, check_authentication,
    plot_mastery_gauge, plot_progress_line, plot_topic_performance
)
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Progress", page_icon="📊", layout="wide")

init_session_state()
check_authentication()

api_client = get_api_client()
user = st.session_state.user

st.title("📊 Your Learning Progress")

# Get data
with st.spinner("Loading analytics..."):
    overview = api_client.get_student_overview(user['id'])
    progress_data = api_client.get_student_progress(user['id'], days=30)
    topic_data = api_client.get_topic_breakdown(user['id'])

# Overall metrics
st.subheader("📈 Overall Performance")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Questions", overview['total_questions'])

with col2:
    st.metric("Correct Answers", overview['correct_answers'])

with col3:
    st.metric("Accuracy", f"{overview['accuracy']}%")

with col4:
    st.metric("Study Time", f"{overview['total_time_seconds']//60} min")

with col5:
    st.metric("Current Streak", f"{overview['current_streak']} days")

st.markdown("---")

# Progress visualization
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📉 Performance Trend")

    if progress_data['data']:
        fig = plot_progress_line(progress_data['data'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Practice more to see your progress trend!")

with col_right:
    st.subheader("🎯 Overall Mastery")

    # Calculate average mastery
    if topic_data['topics']:
        avg_mastery = sum(t['mastery_level'] for t in topic_data['topics']) / len(topic_data['topics'])
        fig = plot_mastery_gauge(avg_mastery, "Average Mastery")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start practicing to build mastery!")

st.markdown("---")

# Topic breakdown
st.subheader("📚 Performance by Topic")

if topic_data['topics']:
    # Bar chart
    fig = plot_topic_performance(topic_data['topics'])
    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.subheader("📋 Detailed Breakdown")

    import pandas as pd
    df = pd.DataFrame(topic_data['topics'])

    # Format columns
    df['mastery_level'] = df['mastery_level'].apply(lambda x: f"{x*100:.1f}%")
    df['accuracy'] = df['accuracy'].apply(lambda x: f"{x:.1f}%")
    df['needs_review'] = df['needs_review'].apply(lambda x: "⚠️ Yes" if x else "✅ No")

    # Rename columns
    df = df.rename(columns={
        'topic': 'Topic',
        'attempts': 'Questions',
        'correct': 'Correct',
        'accuracy': 'Accuracy',
        'mastery_level': 'Mastery',
        'needs_review': 'Needs Review'
    })

    st.dataframe(
        df[['Topic', 'Questions', 'Correct', 'Accuracy', 'Mastery', 'Needs Review']],
        use_container_width=True,
        hide_index=True
    )

    # Topics needing attention
    needs_review = [t for t in topic_data['topics'] if t['needs_review']]

    if needs_review:
        st.warning(f"⚠️ {len(needs_review)} topic(s) need more practice")

        cols = st.columns(min(3, len(needs_review)))
        for idx, topic in enumerate(needs_review[:3]):
            with cols[idx]:
                st.metric(
                    topic['topic'],
                    f"{topic['mastery_level']*100:.0f}%",
                    delta=f"{topic['accuracy']:.0f}% accuracy",
                    delta_color="normal"
                )

else:
    st.info("👉 Start practicing to see your topic breakdown!")

st.markdown("---")

# Study tips
st.subheader("💡 Personalized Study Tips")

try:
    tips = api_client.get_study_tips(user['id'])

    if tips.get('tips'):
        st.success("🎯 **AI-Generated Study Recommendations**")
        st.write(tips['tips'])

        if tips.get('weak_areas'):
            st.write("**Focus areas:**", ", ".join(tips['weak_areas']))
    else:
        st.info(tips.get('message', 'Keep up the great work!'))
except:
    st.info("Practice to get personalized study tips!")

# Action buttons
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("📝 Practice More", type="primary", use_container_width=True):
        st.switch_page("pages/1_📝_Practice.py")

with col2:
    if st.button("🎯 View Learning Path", use_container_width=True):
        st.switch_page("pages/3_🎯_Learning_Path.py")
