from typing import List, Tuple
import numpy as np

class DifficultyAdapter:
    """
    Adapts question difficulty based on student performance
    Maintains optimal challenge level (Flow State Theory)
    """

    def __init__(
        self,
        target_success_rate: float = 0.7,  # Optimal challenge
        adjustment_rate: float = 0.3        # How quickly to adapt
    ):
        """
        Initialize adapter

        Args:
            target_success_rate: Target success rate (0.7 = 70%)
            adjustment_rate: Rate of difficulty adjustment
        """
        self.target_success_rate = target_success_rate
        self.adjustment_rate = adjustment_rate

    def recommend_difficulty(
        self,
        topic_mastery: float,
        recent_performance: List[bool],
        current_difficulty: int = None
    ) -> int:
        """
        Recommend optimal difficulty level

        Args:
            topic_mastery: Current mastery level (0-1)
            recent_performance: List of recent results [True, False, True, ...]
            current_difficulty: Current difficulty level (1-5)

        Returns:
            Recommended difficulty (1-5)
        """

        # If no recent performance, base on mastery
        if not recent_performance or len(recent_performance) < 3:
            return self._difficulty_from_mastery(topic_mastery)

        # Calculate recent success rate
        recent_success_rate = sum(recent_performance) / len(recent_performance)

        # If no current difficulty, estimate from mastery
        if current_difficulty is None:
            current_difficulty = self._difficulty_from_mastery(topic_mastery)

        # Determine adjustment
        if recent_success_rate > 0.85:
            # Too easy - increase difficulty
            adjustment = +1
        elif recent_success_rate < 0.5:
            # Too hard - decrease difficulty
            adjustment = -1
        elif recent_success_rate > 0.75:
            # Slightly easy - small increase
            adjustment = +0.5 if np.random.random() < 0.3 else 0
        elif recent_success_rate < 0.65:
            # Slightly hard - small decrease
            adjustment = -0.5 if np.random.random() < 0.3 else 0
        else:
            # Just right!
            adjustment = 0

        # Apply adjustment with smoothing
        new_difficulty = current_difficulty + (adjustment * self.adjustment_rate)

        # Consider mastery level (don't go too far from mastery-based difficulty)
        mastery_difficulty = self._difficulty_from_mastery(topic_mastery)

        # Weighted average (70% performance-based, 30% mastery-based)
        final_difficulty = 0.7 * new_difficulty + 0.3 * mastery_difficulty

        # Round and clamp to valid range
        return max(1, min(5, round(final_difficulty)))

    def _difficulty_from_mastery(self, mastery: float) -> int:
        """
        Map mastery level to difficulty

        Args:
            mastery: Mastery level (0-1)

        Returns:
            Difficulty level (1-5)
        """
        if mastery < 0.2:
            return 1
        elif mastery < 0.4:
            return 2
        elif mastery < 0.6:
            return 3
        elif mastery < 0.8:
            return 4
        else:
            return 5

    def should_review_easier(
        self,
        consecutive_wrong: int,
        mastery: float
    ) -> bool:
        """
        Determine if student should review easier material

        Args:
            consecutive_wrong: Number of consecutive wrong answers
            mastery: Current mastery level

        Returns:
            True if should review easier material
        """
        # If struggling (3+ wrong in a row) and low mastery
        if consecutive_wrong >= 3 and mastery < 0.5:
            return True

        # If many wrong in a row regardless of mastery
        if consecutive_wrong >= 5:
            return True

        return False

    def calculate_flow_state(
        self,
        difficulty: int,
        mastery: float
    ) -> Tuple[str, float]:
        """
        Assess if student is in optimal learning flow state

        Flow state occurs when challenge matches skill level

        Args:
            difficulty: Current question difficulty
            mastery: Student mastery level

        Returns:
            Tuple of (state_name, flow_score)
            flow_score: 0-1, where 1 is optimal flow
        """
        optimal_difficulty = self._difficulty_from_mastery(mastery)

        difference = abs(difficulty - optimal_difficulty)

        if difference == 0:
            return ("Optimal Flow", 1.0)
        elif difference == 1:
            if difficulty > optimal_difficulty:
                return ("Slightly Challenged", 0.8)
            else:
                return ("Slightly Easy", 0.7)
        elif difference == 2:
            if difficulty > optimal_difficulty:
                return ("Too Challenging", 0.5)
            else:
                return ("Too Easy", 0.6)
        else:
            if difficulty > optimal_difficulty:
                return ("Frustration Zone", 0.2)
            else:
                return ("Boredom Zone", 0.3)

    def get_adaptive_feedback(
        self,
        performance_trend: List[bool],
        current_difficulty: int
    ) -> str:
        """
        Generate adaptive feedback message

        Args:
            performance_trend: Recent performance history
            current_difficulty: Current difficulty level

        Returns:
            Feedback message
        """
        if not performance_trend:
            return "Let's see how you do!"

        recent = performance_trend[-5:]  # Last 5 questions
        success_rate = sum(recent) / len(recent)

        if success_rate >= 0.8:
            return f"Excellent work! Ready for difficulty level {min(5, current_difficulty + 1)}?"
        elif success_rate >= 0.6:
            return "You're doing great! Keep practicing at this level."
        elif success_rate >= 0.4:
            return "Don't worry, learning takes practice. Let's try some easier questions."
        else:
            return "Let's review the basics to build a stronger foundation."

# Global instance
difficulty_adapter = DifficultyAdapter()
