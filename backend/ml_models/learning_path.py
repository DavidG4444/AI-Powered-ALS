from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class LearningPathStep:
    """Single step in learning path"""
    topic: str
    difficulty: int
    estimated_questions: int
    estimated_time_minutes: int
    current_mastery: float
    target_mastery: float
    priority: str  # "High", "Medium", "Low"
    reason: str

class LearningPathGenerator:
    """
    Generates personalized learning paths for students
    """

    def __init__(self):
        self.target_mastery = 0.8  # 80% mastery goal
        self.min_questions_per_topic = 5
        self.avg_time_per_question = 2  # minutes

    def generate_path(
        self,
        knowledge_states: Dict[str, float],
        available_topics: List[str],
        time_available_minutes: Optional[int] = None,
        focus_weak_areas: bool = True
    ) -> List[LearningPathStep]:
        """
        Generate personalized learning path

        Args:
            knowledge_states: Dict of {topic: mastery_level}
            available_topics: All topics with available questions
            time_available_minutes: Optional time constraint
            focus_weak_areas: Whether to prioritize weak areas

        Returns:
            Ordered list of learning steps
        """
        path = []

        # Identify topics needing work
        for topic in available_topics:
            mastery = knowledge_states.get(topic, 0.5)

            # Calculate gap and priority
            gap = self.target_mastery - mastery

            if gap > 0:  # Needs improvement
                # Estimate questions needed
                estimated_questions = self._estimate_questions_needed(
                    mastery,
                    self.target_mastery
                )

                # Determine priority
                priority = self._calculate_priority(mastery, gap)

                # Determine starting difficulty
                difficulty = self._recommend_starting_difficulty(mastery)

                # Generate reason
                reason = self._generate_reason(mastery, gap)

                step = LearningPathStep(
                    topic=topic,
                    difficulty=difficulty,
                    estimated_questions=estimated_questions,
                    estimated_time_minutes=estimated_questions * self.avg_time_per_question,
                    current_mastery=mastery,
                    target_mastery=self.target_mastery,
                    priority=priority,
                    reason=reason
                )

                path.append(step)

        # Sort by priority if focusing on weak areas
        if focus_weak_areas:
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            path.sort(key=lambda x: (priority_order[x.priority], x.current_mastery))
        else:
            # Random order for variety
            import random
            random.shuffle(path)

        # Apply time constraint if specified
        if time_available_minutes:
            path = self._apply_time_constraint(path, time_available_minutes)

        return path

    def _estimate_questions_needed(
        self,
        current_mastery: float,
        target_mastery: float
    ) -> int:
        """
        Estimate number of practice questions needed

        Uses logarithmic model (harder to improve as mastery increases)
        """
        if current_mastery >= target_mastery:
            return 5  # Maintenance practice

        gap = target_mastery - current_mastery

        # Base questions needed (5-30 range)
        base_questions = int(gap * 50)

        # Harder to improve at higher mastery levels
        difficulty_factor = 1 + current_mastery

        total = int(base_questions * difficulty_factor)

        return max(self.min_questions_per_topic, min(50, total))

    def _calculate_priority(self, mastery: float, gap: float) -> str:
        """
        Calculate learning priority

        Args:
            mastery: Current mastery level
            gap: Gap to target mastery

        Returns:
            Priority level: "High", "Medium", or "Low"
        """
        if mastery < 0.4:
            return "High"  # Critical gap
        elif mastery < 0.6:
            return "Medium" if gap > 0.2 else "Low"
        else:
            return "Low"  # Maintenance level

    def _recommend_starting_difficulty(self, mastery: float) -> int:
        """Map mastery to starting difficulty"""
        if mastery < 0.3:
            return 1
        elif mastery < 0.5:
            return 2
        elif mastery < 0.7:
            return 3
        elif mastery < 0.85:
            return 4
        else:
            return 5

    def _generate_reason(self, mastery: float, gap: float) -> str:
        """Generate explanation for why this is in learning path"""
        if mastery < 0.3:
            return "Fundamental concepts need attention - building strong foundation"
        elif mastery < 0.5:
            return "Developing understanding - focus on core principles"
        elif mastery < 0.7:
            return "Approaching proficiency - practice to solidify knowledge"
        elif gap > 0.1:
            return "Almost there - polish your skills to reach mastery"
        else:
            return "Maintenance practice - keep skills sharp"

    def _apply_time_constraint(
        self,
        path: List[LearningPathStep],
        time_available: int
    ) -> List[LearningPathStep]:
        """
        Fit learning path into available time

        Prioritizes high-priority items
        """
        constrained_path = []
        time_used = 0

        for step in path:
            if time_used + step.estimated_time_minutes <= time_available:
                constrained_path.append(step)
                time_used += step.estimated_time_minutes
            elif step.priority == "High":
                # Reduce questions for high-priority items to fit
                remaining_time = time_available - time_used
                if remaining_time >= self.min_questions_per_topic * self.avg_time_per_question:
                    adjusted_questions = remaining_time // self.avg_time_per_question
                    step.estimated_questions = int(adjusted_questions)
                    step.estimated_time_minutes = remaining_time
                    constrained_path.append(step)
                    break

        return constrained_path

    def generate_study_schedule(
        self,
        path: List[LearningPathStep],
        days_available: int,
        daily_time_minutes: int
    ) -> Dict[str, List[LearningPathStep]]:
        """
        Distribute learning path across multiple days

        Args:
            path: Complete learning path
            days_available: Number of days to spread learning
            daily_time_minutes: Time available per day

        Returns:
            Dict of {day: [steps]}
        """
        schedule = {}
        current_day = 0
        daily_time_used = 0
        daily_steps = []

        for step in path:
            if daily_time_used + step.estimated_time_minutes > daily_time_minutes:
                # Start new day
                if daily_steps:
                    schedule[f"Day {current_day + 1}"] = daily_steps
                    current_day += 1
                    daily_steps = []
                    daily_time_used = 0

                if current_day >= days_available:
                    break

            daily_steps.append(step)
            daily_time_used += step.estimated_time_minutes

        # Add remaining steps
        if daily_steps and current_day < days_available:
            schedule[f"Day {current_day + 1}"] = daily_steps

        return schedule

# Global instance
learning_path_generator = LearningPathGenerator()
