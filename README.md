# 🎓 AI-Powered Adaptive Learning System

An intelligent learning platform that personalizes education using machine learning and AI to identify knowledge gaps, adapt difficulty, and provide personalized feedback.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### For Students
- 🤖 **AI-Powered Explanations** - Personalized feedback from Groq AI
- 📊 **Smart Analytics** - Track progress with detailed insights
- 🎯 **Adaptive Learning** - Questions adjust to your skill level
- 💡 **Intelligent Hints** - Get help without revealing answers
- 🗺️ **Learning Paths** - Personalized study recommendations
- 📈 **Progress Tracking** - Visual dashboards and trends

### For Teachers
- 👥 **Student Monitoring** - Track class performance
- 🚨 **Early Intervention** - Identify struggling students
- 📉 **Topic Analysis** - See which topics are hardest
- 🏆 **Leaderboards** - Gamify learning experience
- 📧 **Engagement Tools** - Send encouragement to students

## 🏗️ Architecture
```
├── Backend (FastAPI)
│   ├── REST API endpoints
│   ├── Groq AI integration
│   ├── Bayesian Knowledge Tracking
│   ├── PostgreSQL database
│   └── Analytics engine
│
└── Frontend (Streamlit)
    ├── Student dashboard
    ├── Interactive quiz
    ├── Progress visualization
    └── Teacher portal
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database (Aiven recommended)
- Groq API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/adaptive-learning-system.git
cd adaptive-learning-system
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure Environment**

Create `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
```

4. **Initialize Database**
```bash
python database.py
python load_questions.py
python create_teacher.py
```

5. **Start Backend**
```bash
uvicorn main:app --reload
```

6. **Start Frontend** (new terminal)
```bash
cd ../frontend
streamlit run Home.py
```

## 📚 Usage

### Student Flow
1. Register/Login
2. Take adaptive quiz
3. Receive AI-powered feedback
4. Track progress
5. Follow learning path

### Teacher Flow
1. Login with teacher account
2. View class analytics
3. Identify struggling students
4. Analyze topic difficulty
5. Send encouragement

## 🧠 ML Models

### Bayesian Knowledge Tracking (BKT)
Tracks student knowledge state using probabilistic model:
- P(knows | correct answer)
- P(knows | incorrect answer)
- Accounts for learning and forgetting

### Difficulty Adaptation
Maintains optimal challenge level (Flow State Theory):
- Target: 70% success rate
- Adjusts based on recent performance
- Prevents frustration and boredom

### Learning Path Generator
Creates personalized study plans:
- Identifies knowledge gaps
- Prioritizes weak areas
- Estimates time to mastery

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | PostgreSQL (Aiven) |
| AI | Groq API (Llama 3.3) |
| ML | scikit-learn, Custom BKT |
| Visualization | Plotly |
| Authentication | JWT |

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new student
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Questions
- `GET /api/questions/next` - Get recommended question
- `POST /api/submit-answer` - Submit answer
- `GET /api/questions/{id}/hint` - Get AI hint

### Analytics
- `GET /api/analytics/student/{id}/overview` - Student stats
- `GET /api/analytics/student/{id}/progress` - Progress trend
- `GET /api/students/{id}/learning-path` - Learning path

### Teacher
- `GET /api/teacher/dashboard` - Complete dashboard
- `GET /api/teacher/struggling-students` - Students needing help
- `GET /api/teacher/topic-analysis` - Topic difficulty

## 📝 Demo Credentials

**Student:**
- Username: `testuser`
- Password: `test123`

**Teacher:**
- Username: `teacher`
- Password: `teacher123`

## 🎯 Project Structure
```
adaptive-learning-system/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication
│   ├── ai/
│   │   └── groq_client.py   # Groq AI integration
│   ├── ml_models/
│   │   ├── knowledge_tracker.py
│   │   ├── difficulty_adapter.py
│   │   └── learning_path.py
│   ├── services/
│   │   └── analytics_service.py
│   └── utils/
│       ├── question_loader.py
│       └── recommender.py
│
└── frontend/
    ├── Home.py              # Main dashboard
    ├── pages/
    │   ├── 1_📝_Practice.py
    │   ├── 2_📊_Progress.py
    │   ├── 3_🎯_Learning_Path.py
    │   └── 4_👨‍🏫_Teacher_Dashboard.py
    └── utils/
        ├── api_client.py
        └── helpers.py
```

## 🧪 Testing
```bash
# Run backend tests
cd backend
pytest

# Generate analytics report
python generate_report.py

# Load sample questions
python load_questions.py
```

## 📈 Performance

- **Question Recommendation**: <100ms
- **AI Explanation Generation**: ~2s
- **Analytics Queries**: <500ms
- **Knowledge State Update**: <50ms

## 🔒 Security

- JWT authentication
- Password hashing (bcrypt)
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- Environment variable secrets

## 🚀 Deployment

### Option 1: Local Development
```bash
# Backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
streamlit run Home.py
```

### Option 2: Docker (Coming Soon)
```bash
docker-compose up
```

### Option 3: Cloud (Recommended)
- Backend: Railway, Render, or Heroku
- Frontend: Streamlit Cloud
- Database: Aiven PostgreSQL

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Your Name**
- Portfolio: [yourwebsite.com](https://yourwebsite.com)
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Groq for AI API
- Aiven for database hosting
- FastAPI and Streamlit communities
- Research on Intelligent Tutoring Systems

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Email: your.email@example.com

## 🗺️ Roadmap

- [ ] Mobile app
- [ ] Voice-based quiz
- [ ] Collaborative learning
- [ ] Content creation tools
- [ ] Spaced repetition algorithm
- [ ] Multi-language support

---

**Built with ❤️ using FastAPI, Streamlit, and Groq AI**
