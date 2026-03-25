import streamlit as st
from utils.api_client import get_api_client
from utils.helpers import init_session_state, check_authentication
import time
from datetime import datetime

st.set_page_config(page_title="Practice", page_icon="📝", layout="wide")

init_session_state()
check_authentication()

api_client = get_api_client()
user = st.session_state.user

st.title("📝 Practice Questions")

# Topic selector
topics = api_client.get_topics()
selected_topic = st.selectbox(
    "Choose a topic (or leave blank for adaptive selection)",
    ["Auto-select based on your weaknesses"] + topics
)

if selected_topic == "Auto-select based on your weaknesses":
    selected_topic = None

# Load question
if 'current_question' not in st.session_state or st.session_state.current_question is None:
    with st.spinner("Loading question..."):
        question = api_client.get_next_question(topic=selected_topic)
        st.session_state.current_question = question
        st.session_state.start_time = datetime.now()
        st.session_state.answer_submitted = False
        st.session_state.show_hint = False

question = st.session_state.current_question
# Backward compatibility: some routes may return a list of questions
if isinstance(question, list):
    if len(question) == 0:
        st.error("No questions are available right now. Please try again later.")
        st.stop()
    question = question[0]
    st.session_state.current_question = question
    
# Display question
st.info(f"**Topic:** {question['topic']} | **Difficulty:** {'⭐' * question['difficulty']}")

st.markdown(f"### {question['question_text']}")

# Show hint button
col1, col2 = st.columns([3, 1])
with col2:
    if not st.session_state.get('answer_submitted', False):
        if st.button("💡 Need a hint?"):
            st.session_state.show_hint = True

if st.session_state.get('show_hint', False) and not st.session_state.get('answer_submitted', False):
    with st.spinner("Getting hint..."):
        hint_data = api_client.get_question_hint(question['id'])
        st.success(f"💡 **Hint:** {hint_data['hint']}")

# Answer options
if not st.session_state.get('answer_submitted', False):
    options = [
        f"A) {question['option_a']}",
        f"B) {question['option_b']}",
        f"C) {question['option_c']}",
        f"D) {question['option_d']}"
    ]

    answer = st.radio("Your answer:", options, key="answer_radio")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Submit Answer", type="primary", use_container_width=True):
            # Calculate time taken
            time_taken = (datetime.now() - st.session_state.start_time).seconds

            # Extract answer letter
            answer_letter = answer[0]  # A, B, C, or D

            # Submit
            with st.spinner("Checking answer..."):
                result = api_client.submit_answer(
                    student_id=user['id'],
                    question_id=question['id'],
                    answer=answer_letter,
                    time_taken=time_taken
                )

                st.session_state.result = result
                st.session_state.answer_submitted = True
                st.rerun()

    with col2:
        if st.button("Skip Question", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.show_hint = False
            st.rerun()

# Show result
if st.session_state.get('answer_submitted', False):
    result = st.session_state.result

    if result['correct']:
        st.success("✅ **Correct!** Great job!")
        st.balloons()

        # Show mastery update
        mastery_change = result['mastery_change']
        if mastery_change > 0:
            st.info(f"📈 Your mastery increased by {mastery_change*100:.1f}% → Now at {result['new_mastery_level']*100:.0f}%")

    else:
        st.error("❌ **Incorrect**")

        # Show correct answer
        st.info(f"**Correct Answer:** {result['correct_answer']}")

        # Show explanation
        if result.get('explanation'):
            with st.expander("📖 Explanation", expanded=True):
                st.write(result['explanation'])

        # Show AI explanation
        if result.get('ai_explanation'):
            with st.expander("🤖 AI Tutor Explanation", expanded=True):
                st.write(result['ai_explanation'])

        # Show mastery update
        mastery_change = result['mastery_change']
        if mastery_change < 0:
            st.warning(f"📉 Your mastery decreased by {abs(mastery_change)*100:.1f}% → Now at {result['new_mastery_level']*100:.0f}%")

        if result.get('needs_review'):
            st.warning("⚠️ This topic needs more practice!")

    # Next question button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("➡️ Next Question", type="primary", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.answer_submitted = False
            st.session_state.show_hint = False
            st.rerun()

    with col2:
        if st.button("📊 View Progress", use_container_width=True):
            st.switch_page("pages/2_📊_Progress.py")

    with col3:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.switch_page("Home.py")
