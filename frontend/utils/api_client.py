import requests
from typing import Optional, Dict, List
import streamlit as st

class APIClient:
    """
    Client for interacting with FastAPI backend
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def _get_headers(self) -> Dict:
        """Get headers with authentication token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ===== AUTHENTICATION =====

    def register(self, username: str, email: str, password: str, full_name: str = None) -> Dict:
        """Register new student"""
        response = requests.post(
            f"{self.base_url}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json()

    def login(self, username: str, password: str) -> bool:
        """Login and store token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data={
                    "username": username,
                    "password": password
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]

                # Get user info
                user_info = self.get_current_user()

                # Store in session
                st.session_state.token = self.token
                st.session_state.user = user_info
                st.session_state.logged_in = True

                return True
            return False
        except Exception as e:
            st.error(f"Login error: {e}")
            return False

    def get_current_user(self) -> Dict:
        """Get current user info"""
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self._get_headers()
        )
        return response.json()

    # ===== QUESTIONS =====

    def get_next_question(self, topic: Optional[str] = None) -> Dict:
        """Get next recommended question"""
        params = {"topic": topic} if topic else {}
        response = requests.get(
            f"{self.base_url}/api/questions/next",
            headers=self._get_headers(),
            params=params
        )
        return response.json()

    def get_question_hint(self, question_id: int) -> Dict:
        """Get hint for question"""
        response = requests.get(
            f"{self.base_url}/api/questions/{question_id}/hint",
            headers=self._get_headers()
        )
        return response.json()

    def submit_answer(self, student_id: int, question_id: int, answer: str, time_taken: int) -> Dict:
        """Submit answer"""
        response = requests.post(
            f"{self.base_url}/api/submit-answer",
            headers=self._get_headers(),
            json={
                "student_id": student_id,
                "question_id": question_id,
                "answer_given": answer,
                "time_taken_seconds": time_taken
            }
        )
        return response.json()

    def get_topics(self) -> List[str]:
        """Get all available topics"""
        response = requests.get(f"{self.base_url}/api/topics")
        return response.json()["topics"]

    # ===== ANALYTICS =====

    def get_student_overview(self, student_id: int) -> Dict:
        """Get student analytics overview"""
        response = requests.get(
            f"{self.base_url}/api/analytics/student/{student_id}/overview",
            headers=self._get_headers()
        )
        return response.json()

    def get_student_progress(self, student_id: int, days: int = 30) -> Dict:
        """Get progress over time"""
        response = requests.get(
            f"{self.base_url}/api/analytics/student/{student_id}/progress",
            headers=self._get_headers(),
            params={"days": days}
        )
        return response.json()

    def get_topic_breakdown(self, student_id: int) -> Dict:
        """Get topic breakdown"""
        response = requests.get(
            f"{self.base_url}/api/analytics/student/{student_id}/topics",
            headers=self._get_headers()
        )
        return response.json()

    def get_learning_path(self, student_id: int, time_available: Optional[int] = None) -> Dict:
        """Get personalized learning path"""
        params = {"time_available": time_available} if time_available else {}
        response = requests.get(
            f"{self.base_url}/api/students/{student_id}/learning-path",
            headers=self._get_headers(),
            params=params
        )
        return response.json()

    def get_knowledge_gaps(self) -> Dict:
        """Get knowledge gap analysis"""
        response = requests.get(
            f"{self.base_url}/api/knowledge-gaps",
            headers=self._get_headers()
        )
        return response.json()

    def get_study_tips(self, student_id: int) -> Dict:
        """Get AI-generated study tips"""
        response = requests.get(
            f"{self.base_url}/api/students/{student_id}/study-tips",
            headers=self._get_headers()
        )
        return response.json()

    # ===== TEACHER DASHBOARD =====

    def get_teacher_dashboard(self) -> Dict:
        """Get teacher dashboard data"""
        response = requests.get(
            f"{self.base_url}/api/teacher/dashboard",
            headers=self._get_headers()
        )
        return response.json()

    def get_struggling_students(self, threshold: float = 0.4) -> Dict:
        """Get struggling students"""
        response = requests.get(
            f"{self.base_url}/api/teacher/struggling-students",
            headers=self._get_headers(),
            params={"mastery_threshold": threshold}
        )
        return response.json()

    def get_topic_analysis(self) -> Dict:
        """Get topic difficulty analysis"""
        response = requests.get(
            f"{self.base_url}/api/teacher/topic-analysis",
            headers=self._get_headers()
        )
        return response.json()

    def get_leaderboard(self, metric: str = "accuracy", limit: int = 10) -> Dict:
        """Get leaderboard"""
        response = requests.get(
            f"{self.base_url}/api/leaderboard",
            headers=self._get_headers(),
            params={"metric": metric, "limit": limit}
        )
        return response.json()

# Global API client
def get_api_client() -> APIClient:
    """Get or create API client"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()

    # Restore token if exists
    if 'token' in st.session_state and st.session_state.token:
        st.session_state.api_client.token = st.session_state.token

    return st.session_state.api_client
