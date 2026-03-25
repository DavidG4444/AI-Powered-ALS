"""
Generate analytics report
Run with: python generate_report.py
"""
from database import SessionLocal
from services.analytics_service import AnalyticsService
from datetime import datetime

def generate_report():
    print("="*80)
    print(f"ADAPTIVE LEARNING SYSTEM - ANALYTICS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    db = SessionLocal()
    analytics = AnalyticsService(db)

    try:
        # Class Overview
        print("\n📊 CLASS OVERVIEW")
        print("-"*80)
        overview = analytics.get_class_overview()
        print(f"Total Students: {overview['total_students']}")
        print(f"Active Students (Last 7 Days): {overview['active_students']}")
        print(f"Total Questions Answered: {overview['total_questions_answered']}")
        print(f"Overall Class Accuracy: {overview['overall_accuracy']}%")
        print(f"Average Class Mastery: {overview['avg_class_mastery']}")

        # Topic Difficulty
        print("\n📈 TOPIC DIFFICULTY ANALYSIS")
        print("-"*80)
        topics = analytics.get_topic_difficulty_analysis()
        print(f"{'Topic':<30} {'Students':<10} {'Success Rate':<15} {'Difficulty':<15}")
        print("-"*80)
        for topic in topics[:10]:  # Top 10
            print(f"{topic['topic']:<30} {topic['num_students']:<10} {topic['success_rate']:<14.1f}% {topic['difficulty_rating']:<15}")

        # Struggling Students
        print("\n🚨 STUDENTS NEEDING ATTENTION")
        print("-"*80)
        struggling = analytics.get_struggling_students(mastery_threshold=0.5, min_attempts=5)
        if struggling:
            print(f"{'Student':<20} {'Topic':<25} {'Mastery':<10} {'Accuracy':<10}")
            print("-"*80)
            for student in struggling[:10]:  # Top 10
                print(f"{student['username']:<20} {student['struggling_topic']:<25} {student['mastery_level']:<9.1f} {student['accuracy']:<9.1f}%")
        else:
            print("✅ All students are performing well!")

        # Inactive Students
        print("\n💤 INACTIVE STUDENTS (Last 7 Days)")
        print("-"*80)
        inactive = analytics.get_inactive_students(days=7)
        if inactive:
            print(f"{'Student':<20} {'Email':<30} {'Days Inactive':<15}")
            print("-"*80)
            for student in inactive[:10]:
                days = student['days_inactive'] if student['days_inactive'] else "Never Active"
                print(f"{student['username']:<20} {student['email']:<30} {days:<15}")
        else:
            print("✅ All students are active!")

        # Common Mistakes
        print("\n❌ COMMON MISTAKES")
        print("-"*80)
        mistakes = analytics.get_common_mistakes(limit=5)
        if mistakes:
            for i, mistake in enumerate(mistakes, 1):
                print(f"\n{i}. Topic: {mistake['topic']}")
                print(f"   Question: {mistake['question']}")
                print(f"   Correct: {mistake['correct_answer']} | Common Wrong Answer: {mistake['common_wrong_answer']}")
                print(f"   Students Affected: {mistake['students_affected']}")
        else:
            print("✅ No common mistake patterns found!")

    except Exception as e:
        print(f"\n❌ Error generating report: {e}")

    finally:
        db.close()

    print("\n" + "="*80)
    print("END OF REPORT")
    print("="*80)

if __name__ == "__main__":
    generate_report()
