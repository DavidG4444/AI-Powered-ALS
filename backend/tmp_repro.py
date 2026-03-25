from database import get_db, init_db
from models import Student, Interaction
from sqlalchemy import func, case, desc

if __name__ == '__main__':
    db = next(get_db())
    init_db()
    try:
        q = db.query(
            Student.id,
            Student.username,
            func.count(Interaction.id).label('total_questions'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct'),
            (func.sum(case((Interaction.is_correct == True, 1.0), else_=0.0))/func.count(Interaction.id)*100).label('accuracy')
        ).join(Interaction, Interaction.student_id == Student.id).group_by(Student.id, Student.username).having(func.count(Interaction.id) >= 10).order_by(desc('accuracy')).limit(10)
        print('query defined', q)
        print('result', q.all())
    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        db.close()
