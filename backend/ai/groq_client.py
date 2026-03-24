from groq import Groq
import os
from typing import Optional
from config import get_settings

settings = get_settings()

class GroqAIClient:
    """
    Client for interacting with Groq API
    Generates personalized explanations, hints, and practice questions
    """

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"  # Fast and accurate

    def generate_explanation(
        self,
        question_text: str,
        correct_answer: str,
        student_answer: str,
        topic: str,
        explanation: Optional[str] = None
    ) -> str:
        """
        Generate personalized explanation for why answer was wrong

        Args:
            question_text: The question that was asked
            correct_answer: The correct answer (A, B, C, or D)
            student_answer: What the student answered
            topic: Topic of the question
            explanation: Base explanation from question bank (optional)

        Returns:
            Personalized AI-generated explanation
        """

        # Build context-aware prompt
        prompt = f"""You are a patient and encouraging tutor helping a student learn {topic}.

**Question:** {question_text}

**Student's Answer:** {student_answer}
**Correct Answer:** {correct_answer}

{f'**Base Explanation:** {explanation}' if explanation else ''}

Provide a clear, friendly explanation that:
1. Gently explains why their answer was incorrect (without being discouraging)
2. Clearly explains why the correct answer is right
3. Uses simple language and real-world examples when possible
4. Includes a memory tip or mnemonic if applicable
5. Encourages the student to keep learning

Keep the explanation under 150 words and maintain an encouraging, supportive tone.
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful, patient, and encouraging tutor who explains concepts clearly and builds student confidence."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,  # Balanced creativity
                max_tokens=300,
            )

            explanation = chat_completion.choices[0].message.content
            return explanation.strip()

        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return "I'm having trouble generating an explanation right now. Please review the correct answer and try a similar question."

    def generate_hint(
        self,
        question_text: str,
        topic: str,
        difficulty: int
    ) -> str:
        """
        Generate a subtle hint without giving away the answer

        Args:
            question_text: The question
            topic: Topic of the question
            difficulty: Difficulty level 1-5

        Returns:
            A helpful hint
        """

        prompt = f"""You are helping a student with a {topic} question (difficulty: {difficulty}/5).

**Question:** {question_text}

Provide a subtle hint that:
1. Guides their thinking without revealing the answer
2. Points them toward the right approach
3. Is encouraging and supportive
4. Is 1-2 sentences maximum

Do NOT give the answer directly. Help them think through it.
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a tutor who gives helpful hints without revealing answers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=100,
            )

            hint = chat_completion.choices[0].message.content
            return hint.strip()

        except Exception as e:
            print(f"Error generating hint: {e}")
            return "Think carefully about the question and try to eliminate obviously wrong answers first."

    def generate_encouragement(
        self,
        student_name: str,
        correct_streak: int,
        topic: str,
        mastery_level: float
    ) -> str:
        """
        Generate personalized encouragement message

        Args:
            student_name: Student's name
            correct_streak: Number of consecutive correct answers
            topic: Current topic
            mastery_level: Current mastery level (0.0-1.0)

        Returns:
            Encouraging message
        """

        mastery_percent = int(mastery_level * 100)

        prompt = f"""Generate a short, encouraging message for a student named {student_name}.

Context:
- They just got {correct_streak} questions correct in a row
- Topic: {topic}
- Current mastery: {mastery_percent}%

Create a 1-2 sentence motivational message that:
1. Celebrates their progress
2. Encourages continued learning
3. Is genuine and supportive (not overly cheesy)

Keep it under 30 words.
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an encouraging tutor who celebrates student achievements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.8,
                max_tokens=50,
            )

            encouragement = chat_completion.choices[0].message.content
            return encouragement.strip()

        except Exception as e:
            print(f"Error generating encouragement: {e}")
            return f"Great job, {student_name}! Keep up the excellent work!"

    def generate_study_tips(
        self,
        topic: str,
        weak_areas: list
    ) -> str:
        """
        Generate personalized study tips based on weak areas

        Args:
            topic: Main topic
            weak_areas: List of specific concepts student struggles with

        Returns:
            Study recommendations
        """

        weak_areas_str = ", ".join(weak_areas) if weak_areas else "various concepts"

        prompt = f"""A student is learning {topic} and struggling with: {weak_areas_str}

Provide 3-4 specific, actionable study tips that will help them improve in these areas.

Format as a bulleted list. Each tip should be:
1. Specific and actionable
2. Practical (can be done immediately)
3. Focused on understanding, not memorization
4. Encouraging

Keep the entire response under 150 words.
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced educator providing personalized study advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=250,
            )

            tips = chat_completion.choices[0].message.content
            return tips.strip()

        except Exception as e:
            print(f"Error generating study tips: {e}")
            return "Focus on practicing regularly, reviewing mistakes, and trying to explain concepts in your own words."

# Initialize global client
groq_client = GroqAIClient()
