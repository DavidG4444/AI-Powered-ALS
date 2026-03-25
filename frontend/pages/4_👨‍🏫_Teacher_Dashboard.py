import streamlit as st
from utils.api_client import get_api_client
from utils.helpers import init_session_state, check_authentication
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Teacher Dashboard", page_icon="👨‍🏫", layout="wide")

init_session_state()
check_authentication()

api_client = get_api_client()
user = st.session_state.user

# Check teacher access
if not user.get('is_teacher'):
    st.error("⛔ Teacher access required!")
    st.stop()

st.title("👨‍🏫 Teacher Dashboard")

# Get dashboard data
with st.spinner("Loading class analytics..."):
    dashboard = api_client.get_teacher_dashboard()

# Class overview
st.subheader("📊 Class Overview")

col1, col2, col3, col4 = st.columns(4)

class_overview = dashboard['class_overview']

with col1:
    st.metric("Total Students", class_overview['total_students'])

with col2:
    st.metric("Active Students", class_overview['active_students'])

with col3:
    st.metric("Class Accuracy", f"{class_overview['overall_accuracy']}%")

with col4:
    st.metric("Avg Mastery", f"{class_overview['avg_class_mastery']*100:.0f}%")

st.markdown("---")

# Two columns layout
col_left, col_right = st.columns([2, 1])

with col_left:
    # Struggling students
    st.subheader("🚨 Students Needing Attention")

    struggling = dashboard['struggling_students']

    if struggling:
        # Create DataFrame
        df_struggling = pd.DataFrame(struggling)

        # Format columns
        df_struggling['mastery_level'] = df_struggling['mastery_level'].apply(lambda x: f"{x*100:.0f}%")
        df_struggling['accuracy'] = df_struggling['accuracy'].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            df_struggling[['username', 'struggling_topic', 'mastery_level', 'accuracy', 'total_attempts']],
            use_container_width=True,
            hide_index=True
        )

        # Send help button (placeholder)
        selected_student = st.selectbox(
            "Select student to help:",
            [s['username'] for s in struggling]
        )

        if st.button("📧 Send Encouragement Message", type="primary"):
            st.success(f"✅ Encouragement sent to {selected_student}!")
    else:
        st.success("✅ All students are performing well!")

with col_right:
    # Inactive students
    st.subheader("💤 Inactive Students")

    inactive = dashboard['inactive_students']

    if inactive:
        for student in inactive[:5]:
            days = student.get('days_inactive', 'Never')
            st.warning(f"**{student['username']}**: {days} days inactive")
    else:
        st.success("✅ All students are active!")

st.markdown("---")

# Topic difficulty analysis
st.subheader("📈 Topic Difficulty Analysis")

topic_diff = dashboard['topic_difficulty']

if topic_diff:
    # Create DataFrame
    df_topics = pd.DataFrame(topic_diff)

    # Bar chart
    fig = px.bar(
        df_topics,
        x='topic',
        y='success_rate',
        color='difficulty_rating',
        title="Success Rate by Topic",
        labels={'success_rate': 'Success Rate (%)', 'topic': 'Topic'},
        color_discrete_map={
            'Easy': '#10b981',
            'Medium': '#f59e0b',
            'Hard': '#ef4444'
        }
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    with st.expander("📋 Detailed Topic Statistics"):
        df_display = df_topics[['topic', 'num_students', 'success_rate', 'avg_mastery', 'difficulty_rating']]
        df_display = df_display.rename(columns={
            'topic': 'Topic',
            'num_students': 'Students',
            'success_rate': 'Success Rate (%)',
            'avg_mastery': 'Avg Mastery',
            'difficulty_rating': 'Difficulty'
        })

        st.dataframe(df_display, use_container_width=True, hide_index=True)

st.markdown("---")

# Common mistakes
st.subheader("❌ Common Mistakes")

try:
    mistakes = api_client.get_common_mistakes(limit=5)

    if mistakes['common_mistakes']:
        for idx, mistake in enumerate(mistakes['common_mistakes'], 1):
            with st.expander(f"Mistake #{idx}: {mistake['topic']}"):
                st.write(f"**Question:** {mistake['question']}")
                st.write(f"**Correct Answer:** {mistake['correct_answer']}")
                st.write(f"**Common Wrong Answer:** {mistake['common_wrong_answer']}")
                st.error(f"⚠️ {mistake['students_affected']} students made this mistake")
    else:
        st.success("✅ No common mistake patterns found!")
except:
    st.info("Not enough data for mistake analysis yet")

st.markdown("---")

# Leaderboard
st.subheader("🏆 Leaderboard")

tab1, tab2, tab3 = st.tabs(["By Accuracy", "By Mastery", "By Activity"])

with tab1:
    leaderboard_acc = api_client.get_leaderboard(metric="accuracy", limit=10)

    if leaderboard_acc['leaderboard']:
        for student in leaderboard_acc['leaderboard'][:5]:
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

            with col1:
                if student['rank'] == 1:
                    st.write("🥇")
                elif student['rank'] == 2:
                    st.write("🥈")
                elif student['rank'] == 3:
                    st.write("🥉")
                else:
                    st.write(f"#{student['rank']}")

            with col2:
                st.write(f"**{student['username']}**")

            with col3:
                st.write(f"{student['accuracy']:.1f}%")

            with col4:
                st.write(f"{student['total_questions']} questions")

with tab2:
    leaderboard_mastery = api_client.get_leaderboard(metric="mastery", limit=10)

    if leaderboard_mastery['leaderboard']:
        for student in leaderboard_mastery['leaderboard'][:5]:
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                if student['rank'] == 1:
                    st.write("🥇")
                elif student['rank'] == 2:
                    st.write("🥈")
                elif student['rank'] == 3:
                    st.write("🥉")
                else:
                    st.write(f"#{student['rank']}")

            with col2:
                st.write(f"**{student['username']}**")

            with col3:
                st.write(f"{student['avg_mastery']*100:.0f}% avg mastery")

with tab3:
    leaderboard_questions = api_client.get_leaderboard(metric="questions", limit=10)

    if leaderboard_questions['leaderboard']:
        for student in leaderboard_questions['leaderboard'][:5]:
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                if student['rank'] == 1:
                    st.write("🥇")
                elif student['rank'] == 2:
                    st.write("🥈")
                elif student['rank'] == 3:
                    st.write("🥉")
                else:
                    st.write(f"#{student['rank']}")

            with col2:
                st.write(f"**{student['username']}**")

            with col3:
                st.write(f"{student['total_questions']} questions")

# Action buttons
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Export Report", use_container_width=True):
        st.info("Report export feature coming soon!")

with col2:
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.switch_page("Home.py")
