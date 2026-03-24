import numpy as np
from typing import Dict, List, Tuple

class BayesianKnowledgeTracker:
    """
    Bayesian Knowledge Tracing (BKT) Model

    Tracks student knowledge state using probabilistic model
    Updates beliefs based on student performance
    """

    def __init__(
        self,
        p_learn: float = 0.3,      # Probability of learning from practice
        p_forget: float = 0.05,    # Probability of forgetting
        p_slip: float = 0.1,       # Probability of mistake when knowing
        p_guess: float = 0.25      # Probability of guessing correctly
    ):
        """
        Initialize BKT with parameters

        Args:
            p_learn: Probability student learns concept after practice
            p_forget: Probability student forgets concept
            p_slip: Probability of mistake even when knowing concept
            p_guess: Probability of guessing correct answer
        """
        self.p_learn = p_learn
        self.p_forget = p_forget
        self.p_slip = p_slip
        self.p_guess = p_guess

    def initialize_knowledge(self, prior: float = 0.5) -> float:
        """
        Initialize knowledge state

        Args:
            prior: Initial belief that student knows concept (default 0.5)

        Returns:
            Initial mastery probability
        """
        return prior

    def update_knowledge(
        self,
        current_mastery: float,
        is_correct: bool,
        difficulty: int = 3
    ) -> float:
        """
        Update knowledge state based on answer correctness

        Uses Bayes' theorem to update belief:
        P(knows | answer) = P(answer | knows) * P(knows) / P(answer)

        Args:
            current_mastery: Current probability student knows concept (0-1)
            is_correct: Whether student answered correctly
            difficulty: Question difficulty (1-5), affects learning rate

        Returns:
            Updated mastery probability
        """

        # Adjust learning rate based on difficulty
        # Harder questions -> more learning when correct
        difficulty_factor = difficulty / 3.0
        adjusted_learn = self.p_learn * difficulty_factor

        if is_correct:
            # Student answered correctly
            # P(knows | correct) using Bayes' theorem

            p_correct_if_knows = (1 - self.p_slip)
            p_correct_if_not_knows = self.p_guess

            # Total probability of being correct
            p_correct = (p_correct_if_knows * current_mastery +
                        p_correct_if_not_knows * (1 - current_mastery))

            # Posterior probability of knowing given correct answer
            if p_correct > 0:
                updated = (p_correct_if_knows * current_mastery) / p_correct
            else:
                updated = current_mastery

        else:
            # Student answered incorrectly
            # P(knows | incorrect)

            p_incorrect_if_knows = self.p_slip
            p_incorrect_if_not_knows = (1 - self.p_guess)

            # Total probability of being incorrect
            p_incorrect = (p_incorrect_if_knows * current_mastery +
                          p_incorrect_if_not_knows * (1 - current_mastery))

            # Posterior probability of knowing given incorrect answer
            if p_incorrect > 0:
                updated = (p_incorrect_if_knows * current_mastery) / p_incorrect
            else:
                updated = current_mastery

        # Account for learning (student learns from practice)
        updated = updated + (1 - updated) * adjusted_learn

        # Account for forgetting (small decay)
        updated = updated * (1 - self.p_forget)

        # Ensure bounds [0, 1]
        return np.clip(updated, 0.0, 1.0)

    def predict_performance(
        self,
        mastery: float,
        difficulty: int = 3
    ) -> float:
        """
        Predict probability student will answer correctly

        Args:
            mastery: Current mastery level
            difficulty: Question difficulty

        Returns:
            Probability of correct answer (0-1)
        """
        # Adjust slip probability based on difficulty
        difficulty_factor = difficulty / 3.0
        adjusted_slip = self.p_slip * difficulty_factor

        # P(correct) = P(correct | knows) * P(knows) + P(correct | not knows) * P(not knows)
        p_correct = ((1 - adjusted_slip) * mastery +
                    self.p_guess * (1 - mastery))

        return p_correct

    def identify_knowledge_gaps(
        self,
        topic_mastery: Dict[str, float],
        threshold: float = 0.6
    ) -> List[Dict]:
        """
        Identify topics where student needs more practice

        Args:
            topic_mastery: Dictionary of {topic: mastery_level}
            threshold: Minimum mastery to be considered "learned"

        Returns:
            List of gaps sorted by priority
        """
        gaps = []

        for topic, mastery in topic_mastery.items():
            if mastery < threshold:
                # Calculate urgency score
                urgency = 1 - mastery  # Lower mastery = higher urgency

                gaps.append({
                    'topic': topic,
                    'mastery': mastery,
                    'gap_size': threshold - mastery,
                    'urgency': urgency,
                    'status': self._get_status(mastery)
                })

        # Sort by urgency (most urgent first)
        return sorted(gaps, key=lambda x: x['urgency'], reverse=True)

    def _get_status(self, mastery: float) -> str:
        """Get human-readable status for mastery level"""
        if mastery < 0.3:
            return "Needs Significant Practice"
        elif mastery < 0.5:
            return "Developing Understanding"
        elif mastery < 0.7:
            return "Approaching Proficiency"
        elif mastery < 0.85:
            return "Proficient"
        else:
            return "Mastered"

    def calculate_time_to_mastery(
        self,
        current_mastery: float,
        target_mastery: float = 0.8,
        success_rate: float = 0.7
    ) -> int:
        """
        Estimate number of questions needed to reach mastery

        Args:
            current_mastery: Current mastery level
            target_mastery: Target mastery level
            success_rate: Expected success rate

        Returns:
            Estimated number of practice questions needed
        """
        if current_mastery >= target_mastery:
            return 0

        # Simulate learning trajectory
        mastery = current_mastery
        questions = 0
        max_iterations = 1000  # Safety limit

        while mastery < target_mastery and questions < max_iterations:
            # Simulate answer (weighted by success rate)
            is_correct = np.random.random() < success_rate
            mastery = self.update_knowledge(mastery, is_correct)
            questions += 1

        return questions

# Global instance
knowledge_tracker = BayesianKnowledgeTracker()
