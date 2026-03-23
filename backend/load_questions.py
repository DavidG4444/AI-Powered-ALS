"""
Script to load sample questions into database
Run with: python load_questions.py
"""
from database import SessionLocal, test_connection, init_db
from utils.question_loader import load_sample_questions

def main():
    print("="*60)
    print("LOADING SAMPLE QUESTIONS INTO DATABASE")
    print("="*60)

    # Test connection
    if not test_connection():
        print("❌ Database connection failed!")
        return

    # Initialize database (create tables if needed)
    init_db()

    # Create database session
    db = SessionLocal()

    try:
        # Load questions
        print("\nLoading questions...")
        count = load_sample_questions(db)

        print(f"✅ Successfully loaded {count} questions!")

        # Show summary
        from models import Question
        total = db.query(Question).count()
        topics = db.query(Question.topic).distinct().all()

        print(f"\n📊 Database Summary:")
        print(f"   Total questions: {total}")
        print(f"   Topics: {len(topics)}")
        print(f"   Topic list:")
        for topic in topics:
            topic_count = db.query(Question).filter(Question.topic == topic[0]).count()
            print(f"     - {topic[0]}: {topic_count} questions")

    except Exception as e:
        print(f"❌ Error loading questions: {e}")
        db.rollback()

    finally:
        db.close()

    print("\n" + "="*60)
    print("DONE!")
    print("="*60)

if __name__ == "__main__":
    main()
