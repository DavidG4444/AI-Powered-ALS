from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, desc, extract
from models import Student, Question, Interaction, KnowledgeState
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd

class AnalyticsService:
    """
    Comprehensive analytics service for student performance tracking
    """

    def __init__(self, db: Session):
        self.db = db

    # ===== STUDENT ANALYTICS =====

    def get_student_overview(self, student_id: int) -> Dict:
        """
        Get comprehensive overview of student performance
        """
        # Basic stats
        total_questions = self.db.query(func.count(Interaction.id)).filter(
            Interaction.student_id == student_id
        ).scalar()

        correct_answers = self.db.query(func.count(Interaction.id)).filter(
            and_(
                Interaction.student_id == student_id,
                Interaction.is_correct == True
            )
        ).scalar()

        # Time stats
        total_time = self.db.query(func.sum(Interaction.time_taken_seconds)).filter(
            Interaction.student_id == student_id
        ).scalar() or 0

        avg_time = self.db.query(func.avg(Interaction.time_taken_seconds)).filter(
            Interaction.student_id == student_id
        ).scalar() or 0

        # Recent activity
        last_activity = self.db.query(func.max(Interaction.timestamp)).filter(
            Interaction.student_id == student_id
        ).scalar()

        # Calculate accuracy
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        # Knowledge states summary
        knowledge_states = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id
        ).all()

        topics_mastered = sum(1 for ks in knowledge_states if ks.mastery_level >= 0.8)
        topics_in_progress = sum(1 for ks in knowledge_states if 0.5 <= ks.mastery_level < 0.8)
        topics_struggling = sum(1 for ks in knowledge_states if ks.mastery_level < 0.5)

        # Current streak
        streak = self._calculate_current_streak(student_id)

        return {
            "student_id": student_id,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": round(accuracy, 2),
            "total_time_seconds": total_time,
            "avg_time_per_question": round(avg_time, 1),
            "last_activity": last_activity,
            "current_streak": streak,
            "topics_mastered": topics_mastered,
            "topics_in_progress": topics_in_progress,
            "topics_struggling": topics_struggling,
            "total_topics": len(knowledge_states)
        }

    def get_progress_over_time(
        self,
        student_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        Get daily progress for the last N days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query daily statistics
        daily_stats = self.db.query(
            func.date(Interaction.timestamp).label('date'),
            func.count(Interaction.id).label('questions_attempted'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct'),
            func.avg(Interaction.time_taken_seconds).label('avg_time')
        ).filter(
            and_(
                Interaction.student_id == student_id,
                Interaction.timestamp >= cutoff_date
            )
        ).group_by(
            func.date(Interaction.timestamp)
        ).order_by(
            func.date(Interaction.timestamp)
        ).all()

        results = []
        for stat in daily_stats:
            accuracy = (stat.correct / stat.questions_attempted * 100) if stat.questions_attempted > 0 else 0
            results.append({
                "date": stat.date.isoformat(),
                "questions_attempted": stat.questions_attempted,
                "correct": stat.correct,
                "accuracy": round(accuracy, 2),
                "avg_time_seconds": round(stat.avg_time, 1) if stat.avg_time else 0
            })

        return results

    def get_topic_breakdown(self, student_id: int) -> List[Dict]:
        """
        Get detailed breakdown by topic
        """
        topic_stats = self.db.query(
            Question.topic,
            func.count(Interaction.id).label('attempts'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct'),
            func.avg(Interaction.time_taken_seconds).label('avg_time'),
            KnowledgeState.mastery_level,
            KnowledgeState.needs_review
        ).join(
            Interaction, Interaction.question_id == Question.id
        ).outerjoin(
            KnowledgeState,
            and_(
                KnowledgeState.student_id == student_id,
                KnowledgeState.topic == Question.topic
            )
        ).filter(
            Interaction.student_id == student_id
        ).group_by(
            Question.topic,
            KnowledgeState.mastery_level,
            KnowledgeState.needs_review
        ).all()

        results = []
        for stat in topic_stats:
            accuracy = (stat.correct / stat.attempts * 100) if stat.attempts > 0 else 0
            results.append({
                "topic": stat.topic,
                "attempts": stat.attempts,
                "correct": stat.correct,
                "accuracy": round(accuracy, 2),
                "avg_time_seconds": round(stat.avg_time, 1) if stat.avg_time else 0,
                "mastery_level": round(stat.mastery_level, 2) if stat.mastery_level else 0,
                "needs_review": stat.needs_review if stat.needs_review is not None else False
            })

        return results

    def get_performance_by_difficulty(self, student_id: int) -> List[Dict]:
        """
        Analyze performance across difficulty levels
        """
        difficulty_stats = self.db.query(
            Question.difficulty,
            func.count(Interaction.id).label('attempts'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct'),
            func.avg(Interaction.time_taken_seconds).label('avg_time')
        ).join(
            Interaction, Interaction.question_id == Question.id
        ).filter(
            Interaction.student_id == student_id
        ).group_by(
            Question.difficulty
        ).order_by(
            Question.difficulty
        ).all()

        results = []
        for stat in difficulty_stats:
            accuracy = (stat.correct / stat.attempts * 100) if stat.attempts > 0 else 0
            results.append({
                "difficulty": stat.difficulty,
                "attempts": stat.attempts,
                "correct": stat.correct,
                "accuracy": round(accuracy, 2),
                "avg_time_seconds": round(stat.avg_time, 1) if stat.avg_time else 0
            })

        return results

    def _calculate_current_streak(self, student_id: int) -> int:
        """
        Calculate consecutive days of practice
        """
        # Get last 30 days of activity
        cutoff = datetime.utcnow() - timedelta(days=30)

        activity_dates = self.db.query(
            func.date(Interaction.timestamp).label('date')
        ).filter(
            and_(
                Interaction.student_id == student_id,
                Interaction.timestamp >= cutoff
            )
        ).distinct().order_by(
            desc(func.date(Interaction.timestamp))
        ).all()

        if not activity_dates:
            return 0

        # Check for consecutive days
        streak = 0
        expected_date = datetime.utcnow().date()

        for activity in activity_dates:
            if activity.date == expected_date or activity.date == expected_date - timedelta(days=1):
                streak += 1
                expected_date = activity.date - timedelta(days=1)
            else:
                break

        return streak

    # ===== TEACHER DASHBOARD ANALYTICS =====

    def get_struggling_students(
        self,
        mastery_threshold: float = 0.4,
        min_attempts: int = 5
    ) -> List[Dict]:
        """
        Identify students who need help
        """
        struggling = self.db.query(
            Student.id,
            Student.username,
            Student.email,
            KnowledgeState.topic,
            KnowledgeState.mastery_level,
            func.count(Interaction.id).label('total_attempts'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct_attempts'),
            func.max(Interaction.timestamp).label('last_activity')
        ).join(
            KnowledgeState, KnowledgeState.student_id == Student.id
        ).outerjoin(
            Interaction, Interaction.student_id == Student.id
        ).filter(
            KnowledgeState.mastery_level < mastery_threshold
        ).group_by(
            Student.id,
            Student.username,
            Student.email,
            KnowledgeState.topic,
            KnowledgeState.mastery_level
        ).having(
            func.count(Interaction.id) >= min_attempts
        ).order_by(
            KnowledgeState.mastery_level.asc()
        ).all()

        results = []
        for student in struggling:
            accuracy = (student.correct_attempts / student.total_attempts * 100) if student.total_attempts > 0 else 0
            results.append({
                "student_id": student.id,
                "username": student.username,
                "email": student.email,
                "struggling_topic": student.topic,
                "mastery_level": round(student.mastery_level, 2),
                "total_attempts": student.total_attempts,
                "accuracy": round(accuracy, 2),
                "last_activity": student.last_activity.isoformat() if student.last_activity else None
            })

        return results

    def get_class_overview(self) -> Dict:
        """
        Get overall class statistics
        """
        total_students = self.db.query(func.count(Student.id)).scalar()

        total_questions_answered = self.db.query(func.count(Interaction.id)).scalar()

        overall_accuracy = self.db.query(
            func.avg(case((Interaction.is_correct == True, 1.0), else_=0.0))
        ).scalar()

        avg_mastery = self.db.query(
            func.avg(KnowledgeState.mastery_level)
        ).scalar()

        # Active students (practiced in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_students = self.db.query(
            func.count(func.distinct(Interaction.student_id))
        ).filter(
            Interaction.timestamp >= week_ago
        ).scalar()

        return {
            "total_students": total_students,
            "active_students": active_students,
            "total_questions_answered": total_questions_answered,
            "overall_accuracy": round(overall_accuracy * 100, 2) if overall_accuracy else 0,
            "avg_class_mastery": round(avg_mastery, 2) if avg_mastery else 0
        }

    def get_topic_difficulty_analysis(self) -> List[Dict]:
        """
        Analyze which topics are hardest across all students
        """
        topic_analysis = self.db.query(
            Question.topic,
            func.count(func.distinct(Interaction.student_id)).label('num_students'),
            func.count(Interaction.id).label('total_attempts'),
            func.avg(case((Interaction.is_correct == True, 1.0), else_=0.0)).label('success_rate'),
            func.avg(KnowledgeState.mastery_level).label('avg_mastery'),
            func.avg(Interaction.time_taken_seconds).label('avg_time')
        ).join(
            Interaction, Interaction.question_id == Question.id
        ).outerjoin(
            KnowledgeState,
            and_(
                KnowledgeState.student_id == Interaction.student_id,
                KnowledgeState.topic == Question.topic
            )
        ).group_by(
            Question.topic
        ).having(
            func.count(Interaction.id) >= 10  # At least 10 attempts
        ).order_by(
            desc('success_rate')
        ).all()

        results = []
        for topic in topic_analysis:
            # Determine difficulty rating
            if topic.success_rate > 0.75:
                difficulty_rating = "Easy"
            elif topic.success_rate > 0.55:
                difficulty_rating = "Medium"
            else:
                difficulty_rating = "Hard"

            results.append({
                "topic": topic.topic,
                "num_students": topic.num_students,
                "total_attempts": topic.total_attempts,
                "success_rate": round(topic.success_rate * 100, 2),
                "avg_mastery": round(topic.avg_mastery, 2) if topic.avg_mastery else 0,
                "avg_time_seconds": round(topic.avg_time, 1) if topic.avg_time else 0,
                "difficulty_rating": difficulty_rating
            })

        return results

    def get_inactive_students(self, days: int = 7) -> List[Dict]:
        """
        Find students who haven't practiced recently
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get all students
        all_students = self.db.query(Student).all()

        inactive = []
        for student in all_students:
            last_activity = self.db.query(
                func.max(Interaction.timestamp)
            ).filter(
                Interaction.student_id == student.id
            ).scalar()

            if last_activity is None or last_activity < cutoff_date:
                days_inactive = (datetime.utcnow() - last_activity).days if last_activity else None

                inactive.append({
                    "student_id": student.id,
                    "username": student.username,
                    "email": student.email,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "days_inactive": days_inactive
                })

        return sorted(inactive, key=lambda x: x['days_inactive'] if x['days_inactive'] else 999, reverse=True)

    def get_common_mistakes(
        self,
        topic: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find most common wrong answers
        """
        query = self.db.query(
            Question.question_text,
            Question.topic,
            Question.correct_answer,
            Interaction.answer_given,
            func.count(Interaction.id).label('mistake_count')
        ).join(
            Interaction, Interaction.question_id == Question.id
        ).filter(
            Interaction.is_correct == False
        )

        if topic:
            query = query.filter(Question.topic == topic)

        common_mistakes = query.group_by(
            Question.question_text,
            Question.topic,
            Question.correct_answer,
            Interaction.answer_given
        ).having(
            func.count(Interaction.id) >= 3  # At least 3 students made this mistake
        ).order_by(
            desc('mistake_count')
        ).limit(limit).all()

        results = []
        for mistake in common_mistakes:
            results.append({
                "question": mistake.question_text[:100] + "..." if len(mistake.question_text) > 100 else mistake.question_text,
                "topic": mistake.topic,
                "correct_answer": mistake.correct_answer,
                "common_wrong_answer": mistake.answer_given,
                "students_affected": mistake.mistake_count
            })

        return results

    def compare_student_to_class(self, student_id: int) -> Dict:
        """
        Compare individual student performance to class average
        """
        # Student stats
        student_stats = self.get_student_overview(student_id)

        # Class averages
        class_avg_accuracy = self.db.query(
            func.avg(
                func.cast(
                    func.sum(case((Interaction.is_correct == True, 1), else_=0)),
                    type_=float
                ) / func.count(Interaction.id) * 100
            )
        ).group_by(
            Interaction.student_id
        ).scalar()

        class_avg_mastery = self.db.query(
            func.avg(KnowledgeState.mastery_level)
        ).scalar()

        # Topic comparison
        student_topics = self.db.query(
            KnowledgeState.topic,
            KnowledgeState.mastery_level
        ).filter(
            KnowledgeState.student_id == student_id
        ).all()

        topic_comparison = []
        for topic_data in student_topics:
            class_avg_topic = self.db.query(
                func.avg(KnowledgeState.mastery_level)
            ).filter(
                KnowledgeState.topic == topic_data.topic
            ).scalar()

            difference = topic_data.mastery_level - (class_avg_topic or 0)

            topic_comparison.append({
                "topic": topic_data.topic,
                "student_mastery": round(topic_data.mastery_level, 2),
                "class_average": round(class_avg_topic, 2) if class_avg_topic else 0,
                "difference": round(difference, 2),
                "status": "Above Average" if difference > 0.1 else "Below Average" if difference < -0.1 else "On Par"
            })

        return {
            "student_id": student_id,
            "student_accuracy": student_stats['accuracy'],
            "class_avg_accuracy": round(class_avg_accuracy, 2) if class_avg_accuracy else 0,
            "student_mastery": round(class_avg_mastery, 2) if class_avg_mastery else 0,
            "class_avg_mastery": round(class_avg_mastery, 2) if class_avg_mastery else 0,
            "topic_comparison": topic_comparison
        }

    def get_improvement_trends(
        self,
        student_id: int,
        days: int = 14
    ) -> Dict:
        """
        Analyze if student is improving, declining, or stable
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Split time period in half
        mid_point = datetime.utcnow() - timedelta(days=days//2)

        # First half performance
        first_half = self.db.query(
            func.avg(case((Interaction.is_correct == True, 1.0), else_=0.0))
        ).filter(
            and_(
                Interaction.student_id == student_id,
                Interaction.timestamp >= cutoff_date,
                Interaction.timestamp < mid_point
            )
        ).scalar()

        # Second half performance
        second_half = self.db.query(
            func.avg(case((Interaction.is_correct == True, 1.0), else_=0.0))
        ).filter(
            and_(
                Interaction.student_id == student_id,
                Interaction.timestamp >= mid_point
            )
        ).scalar()

        if first_half is None or second_half is None:
            return {
                "student_id": student_id,
                "trend": "Insufficient Data",
                "change": 0,
                "message": "Need more practice to determine trends"
            }

        change = (second_half - first_half) * 100

        if change > 5:
            trend = "Improving"
            message = "Great progress! Keep up the excellent work."
        elif change < -5:
            trend = "Declining"
            message = "Performance is declining. Consider reviewing basics."
        else:
            trend = "Stable"
            message = "Performance is consistent. Keep practicing!"

        return {
            "student_id": student_id,
            "first_period_accuracy": round(first_half * 100, 2),
            "recent_period_accuracy": round(second_half * 100, 2),
            "trend": trend,
            "change_percent": round(change, 2),
            "message": message
        }
