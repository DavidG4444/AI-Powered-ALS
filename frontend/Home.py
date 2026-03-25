import streamlit as st
from utils.api_client import get_api_client
from utils.helpers import init_session_state, logout, format_time, get_mastery_emoji
import time

# Page config
st.set_page_config(
    page_title="Adaptive Learning System",
    page_icon="🎓",
    layout="wide"
)

# Initialize
init_session_state()
api_client = get_api_client()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ===== LOGIN PAGE =====
if not st.session_state.logged_in:
    st.markdown('<h1 class="main-header">🎓 Adaptive Learning System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Personalized Education</p>', unsafe_allow_html=True)

    # Features
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🤖 **AI-Powered Explanations**\n\nGet personalized feedback from advanced AI")
    with col2:
        st.info("📊 **Smart Analytics**\n\nTrack your progress with detailed insights")
    with col3:
        st.info("🎯 **Adaptive Learning**\n\nQuestions adjust to your skill level")

    st.markdown("---")

    # Login/Register tabs
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if username and password:
                    with st.spinner("Logging in..."):
                        if api_client.login(username, password):
                            st.success("✅ Login successful!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials. Please try again.")
                else:
                    st.warning("Please enter username and password")

        # Demo credentials
        with st.expander("🔑 Demo Credentials"):
            st.code("Username: testuser\nPassword: test123", language=None)
            st.code("Teacher: teacher\nPassword: teacher123", language=None)

    with tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            new_username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            full_name = st.text_input("Full Name (optional)", key="reg_fullname")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

            submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                if new_password != confirm_password:
                    st.error("❌ Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif not new_username or not email:
                    st.warning("⚠️ Username and email are required")
                else:
                    try:
                        result = api_client.register(
                            username=new_username,
                            email=email,
                            password=new_password,
                            full_name=full_name
                        )
                        st.success(f"✅ Account created! Please login as {new_username}")
                    except Exception as e:
                        st.error(f"❌ Registration failed: {str(e)}")

# ===== MAIN DASHBOARD (after login) =====
else:
    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        st.title(f"👋 {user.get('username', 'User')}")
        st.caption(user.get('email', ''))

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.markdown("---")

        # Quick stats
        st.subheader("Quick Stats")
        try:
            stats = api_client.get_student_overview(user['id'])
            st.metric("Questions", stats['total_questions'])
            st.metric("Accuracy", f"{stats['accuracy']}%")
            st.metric("Streak", f"{stats['current_streak']} days")
        except:
            st.info("Practice to see your stats!")

    # Main content
    st.markdown(f'<h1 class="main-header">Welcome back, {user.get("full_name") or user.get("username")}! 🎉</h1>', unsafe_allow_html=True)

    # Get analytics
    try:
        overview = api_client.get_student_overview(user['id'])

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Total Questions",
                overview['total_questions'],
                help="Total questions you've answered"
            )
        with col2:
            st.metric(
                "Accuracy",
                f"{overview['accuracy']}%",
                help="Your overall accuracy"
            )
        with col3:
            st.metric(
                "Topics Mastered",
                f"{overview['topics_mastered']}/{overview['total_topics']}",
                help="Topics with >80% mastery"
            )
        with col4:
            st.metric(
                "Current Streak",
                f"{overview['current_streak']} days",
                help="Consecutive days of practice"
            )

        st.markdown("---")

        # Two columns
        left_col, right_col = st.columns([2, 1])

        with left_col:
            st.subheader("📚 Your Topics")

            # Get topic breakdown
            topic_data = api_client.get_topic_breakdown(user['id'])

            if topic_data['topics']:
                for topic in topic_data['topics'][:5]:  # Top 5
                    mastery = topic['mastery_level']
                    emoji = get_mastery_emoji(mastery)

                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.write(f"{emoji} **{topic['topic']}**")
                    with col_b:
                        st.progress(mastery)
                    with col_c:
                        st.write(f"{int(mastery * 100)}%")
            else:
                st.info("👉 Start practicing to see your progress!")

        with right_col:
            st.subheader("🎯 Quick Actions")

            if st.button("📝 Start Practice", use_container_width=True, type="primary"):
                st.switch_page("pages/1_📝_Practice.py")

            if st.button("📊 View Progress", use_container_width=True):
                st.switch_page("pages/2_📊_Progress.py")

            if st.button("🎯 Learning Path", use_container_width=True):
                st.switch_page("pages/3_🎯_Learning_Path.py")

            # Teacher dashboard button
            if user.get('is_teacher'):
                st.markdown("---")
                if st.button("👨‍🏫 Teacher Dashboard", use_container_width=True):
                    st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")

        # Knowledge gaps
        if overview['topics_struggling'] > 0:
            st.markdown("---")
            st.warning(f"⚠️ You have {overview['topics_struggling']} topic(s) that need attention")

            try:
                gaps = api_client.get_knowledge_gaps()
                if gaps['gaps']:
                    st.write("**Topics needing practice:**")
                    for gap in gaps['gaps'][:3]:
                        st.write(f"• {gap['topic']}: {int(gap['mastery']*100)}% mastery ({gap['status']})")
            except:
                pass

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("👉 Start by practicing some questions!")

        if st.button("Go to Practice", type="primary"):
            st.switch_page("pages/1_📝_Practice.py")
