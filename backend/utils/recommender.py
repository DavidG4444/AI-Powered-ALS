from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from models import Question, KnowledgeState, Interaction
from typing import Optional, List
import random

class QuestionRecommender:
    """
    Recommends next best question for student
    Based on knowledge state and recent performance
    """

    def __init__(self, db: Session):
        self.db = db

    def get_next_question(
        self,
        student_id: int,
        topic: Optional[str] = None
    ) -> Optional[Question]:
        """
        Get the next recommended question for a student

        Algorithm:
        1. If topic specified, filter by topic
        2. Check knowledge states to find weak areas
        3. Recommend appropriate difficulty based on mastery
        4. Avoid recently asked questions
        5. Prioritize questions student hasn't seen
        """

        # Get student's knowledge states
        knowledge_states = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id
        ).all()

        # If no topic specified, choose weakest topic
        if not topic and knowledge_states:
            # Find topic with lowest mastery
            weakest = min(knowledge_states, key=lambda x: x.mastery_level)
            topic = weakest.topic

        # If still no topic, choose random topic with questions
        if not topic:
            all_topics = self.db.query(Question.topic).distinct().all()
            if all_topics:
                topic = random.choice(all_topics)[0]

        # Get knowledge state for this topic
        knowledge_state = None
        if topic:
            knowledge_state = self.db.query(KnowledgeState).filter(
                and_(
                    KnowledgeState.student_id == student_id,
                    KnowledgeState.topic == topic
                )
            ).first()

        # Determine recommended difficulty
        if knowledge_state:
            mastery = knowledge_state.mastery_level

            if mastery < 0.3:
                difficulty = 1  # Beginner
            elif mastery < 0.5:
                difficulty = 2  # Easy-Medium
            elif mastery < 0.7:
                difficulty = 3  # Medium
            elif mastery < 0.85:
                difficulty = 4  # Medium-Hard
            else:
                difficulty = 5  # Advanced
        else:
            difficulty = 1  # Start with easiest for new topics

        # Get questions student hasn't answered yet
        answered_ids = self.db.query(Interaction.question_id).filter(
            Interaction.student_id == student_id
        ).all()
        answered_ids = [qid[0] for qid in answered_ids]

        # Query for suitable questions
        query = self.db.query(Question)

        if topic:
            query = query.filter(Question.topic == topic)

        # Try to get unanswered questions at recommended difficulty
        unanswered = query.filter(
            and_(
                Question.difficulty == difficulty,
                ~Question.id.in_(answered_ids)
            )
        ).all()

        if unanswered:
            return random.choice(unanswered)

        # If no unanswered at that difficulty, try nearby difficulties
        for diff_offset in [1, -1, 2, -2]:
            nearby_diff = max(1, min(5, difficulty + diff_offset))
            nearby = query.filter(
                and_(
                    Question.difficulty == nearby_diff,
                    ~Question.id.in_(answered_ids)
                )
            ).all()

            if nearby:
                return random.choice(nearby)

        # If all questions in topic answered, allow repeats
        all_topic_questions = query.filter(
            Question.difficulty == difficulty
        ).all()

        if all_topic_questions:
            return random.choice(all_topic_questions)

        # Last resort: any question from topic
        any_question = query.first()
        return any_question

    def get_recommended_topics(
        self,
        student_id: int,
        limit: int = 3
    ) -> List[dict]:
        """
        Get list of recommended topics for student to practice

        Returns topics ordered by priority (lowest mastery first)
        """
        knowledge_states = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id
        ).order_by(KnowledgeState.mastery_level.asc()).limit(limit).all()

        recommendations = []
        for ks in knowledge_states:
            recommendations.append({
                'topic': ks.topic,
                'mastery_level': ks.mastery_level,
                'needs_review': ks.needs_review,
                'priority': 'High' if ks.mastery_level < 0.4 else 'Medium' if ks.mastery_level < 0.7 else 'Low'
            })

        return recommendations
