import streamlit as st
from utils.api_client import get_api_client
from utils.helpers import init_session_state, check_authentication, get_mastery_color
import plotly.graph_objects as go

st.set_page_config(page_title="Learning Path", page_icon="🎯", layout="wide")

init_session_state()
check_authentication()

api_client = get_api_client()
user = st.session_state.user

st.title("🎯 Your Personalized Learning Path")

st.write("""
This AI-generated learning path is customized based on your current knowledge state.
Follow this path to improve most efficiently!
""")

# Time constraint (optional)
col1, col2 = st.columns([3, 1])

with col1:
    use_time_constraint = st.checkbox("Set time limit")

with col2:
    time_available = None
    if use_time_constraint:
        time_available = st.number_input(
            "Minutes available",
            min_value=10,
            max_value=300,
            value=60,
            step=10
        )

# Get learning path
with st.spinner("Generating your personalized learning path..."):
    path_data = api_client.get_learning_path(
        user['id'],
        time_available=time_available
    )

if not path_data.get('path'):
    st.success("🎉 Congratulations! You've mastered all available topics!")
    st.balloons()

    if st.button("📝 Practice to Maintain Skills", type="primary"):
        st.switch_page("pages/1_📝_Practice.py")

    st.stop()

path = path_data['path']

# Summary
st.subheader("📋 Learning Path Summary")

total_questions = sum(step['estimated_questions'] for step in path)
total_time = sum(step['estimated_time_minutes'] for step in path)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Topics to Practice", len(path))

with col2:
    st.metric("Estimated Questions", total_questions)

with col3:
    st.metric("Estimated Time", f"{total_time} min")

st.markdown("---")

# Path visualization
st.subheader("🗺️ Your Learning Journey")

# Create roadmap visualization
for idx, step in enumerate(path, 1):
    priority_colors = {
        "High": "#ef4444",
        "Medium": "#f59e0b",
        "Low": "#3b82f6"
    }

    color = priority_colors.get(step['priority'], "#6b7280")

    # Create expander for each step
    with st.expander(
        f"**Step {idx}: {step['topic']}** - {step['priority']} Priority",
        expanded=(idx == 1)  # Expand first step
    ):
        col_a, col_b = st.columns([2, 1])

        with col_a:
            st.write(f"**Why this topic?**")
            st.info(step['reason'])

            st.write(f"**📊 Current Mastery:** {step['current_mastery']*100:.0f}%")
            st.write(f"**🎯 Target Mastery:** {step['target_mastery']*100:.0f}%")

            # Progress bar
            progress = step['current_mastery'] / step['target_mastery']
            st.progress(min(progress, 1.0))

        with col_b:
            st.metric("Questions", step['estimated_questions'])
            st.metric("Time", f"{step['estimated_time_minutes']} min")
            st.metric("Difficulty", "⭐" * step['difficulty'])

        # Start practice button
        if st.button(
            f"▶️ Start Practicing {step['topic']}",
            key=f"practice_{idx}",
            use_container_width=True
        ):
            # Store topic in session and switch to practice
            st.session_state.selected_practice_topic = step['topic']
            st.switch_page("pages/1_📝_Practice.py")

st.markdown("---")

# Knowledge gaps visualization
st.subheader("🔍 Knowledge Gap Analysis")

try:
    gaps = api_client.get_knowledge_gaps()

    if gaps.get('gaps'):
        # Create funnel chart
        topics = [g['topic'] for g in gaps['gaps'][:5]]
        urgency = [g['urgency'] for g in gaps['gaps'][:5]]

        fig = go.Figure(go.Funnel(
            y=topics,
            x=urgency,
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=["#ef4444", "#f59e0b", "#f59e0b", "#3b82f6", "#3b82f6"])
        ))

        fig.update_layout(
            title="Topics by Urgency (Most Urgent at Top)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed gap analysis
        st.write("**Detailed Gap Analysis:**")

        for gap in gaps['gaps'][:5]:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**{gap['topic']}**")
                st.caption(gap['status'])

            with col2:
                st.metric("Mastery", f"{gap['mastery']*100:.0f}%")

            with col3:
                st.metric("Gap", f"{gap['gap_size']*100:.0f}%")
    else:
        st.success("✅ No significant knowledge gaps found!")

except Exception as e:
    st.warning("Complete more questions to see gap analysis")

# Action buttons
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Start First Topic", type="primary", use_container_width=True):
        if path:
            st.session_state.selected_practice_topic = path[0]['topic']
            st.switch_page("pages/1_📝_Practice.py")

with col2:
    if st.button("📊 View Progress", use_container_width=True):
        st.switch_page("pages/2_📊_Progress.py")

with col3:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("Home.py")
