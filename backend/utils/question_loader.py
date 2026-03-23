import json
import random
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from models import Question
import os

class QuestionLoader:
    """
    Utility class for loading and managing questions
    """

    def __init__(self, json_path: str = 'data/sample_questions.json'):
        self.json_path = json_path
        self.questions_data = self._load_json()

    def _load_json(self) -> Dict:
        """Load questions from JSON file"""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"Question file not found: {self.json_path}")

        with open(self.json_path, 'r') as f:
            return json.load(f)

    def load_questions_to_db(self, db: Session, created_by: int = None) -> int:
        """
        Load all questions from JSON into database

        Args:
            db: Database session
            created_by: Student ID who created these questions (optional)

        Returns:
            Number of questions loaded
        """
        count = 0

        for q_data in self.questions_data['questions']:
            # Check if question already exists
            existing = db.query(Question).filter(
                Question.question_text == q_data['question_text']
            ).first()

            if existing:
                continue  # Skip duplicates

            # Create new question
            question = Question(
                topic=q_data['topic'],
                difficulty=q_data['difficulty'],
                question_text=q_data['question_text'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', ''),
                created_by=created_by
            )

            db.add(question)
            count += 1

        db.commit()
        return count

    def get_all_topics(self) -> List[str]:
        """Get list of all unique topics"""
        topics = set()
        for q in self.questions_data['questions']:
            topics.add(q['topic'])
        return sorted(list(topics))

    def get_questions_by_topic(self, topic: str) -> List[Dict]:
        """Get all questions for a specific topic"""
        return [
            q for q in self.questions_data['questions']
            if q['topic'] == topic
        ]

    def get_questions_by_difficulty(self, difficulty: int) -> List[Dict]:
        """Get all questions at a specific difficulty level"""
        return [
            q for q in self.questions_data['questions']
            if q['difficulty'] == difficulty
        ]

    def get_random_question(
        self,
        topic: Optional[str] = None,
        difficulty: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get a random question, optionally filtered by topic and/or difficulty
        """
        questions = self.questions_data['questions']

        # Apply filters
        if topic:
            questions = [q for q in questions if q['topic'] == topic]

        if difficulty:
            questions = [q for q in questions if q['difficulty'] == difficulty]

        if not questions:
            return None

        return random.choice(questions)

# Helper function for easy import
def load_sample_questions(db: Session, created_by: int = None) -> int:
    """
    Convenience function to load sample questions

    Usage:
        from utils.question_loader import load_sample_questions
        count = load_sample_questions(db)
    """
    loader = QuestionLoader()
    return loader.load_questions_to_db(db, created_by)
