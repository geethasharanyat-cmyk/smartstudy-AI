# 🎓 SmartStudy AI: Your Intelligent Personal Study Planner

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit%201.40+-red.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-orange.svg)](https://www.sqlalchemy.org/)
[![AI Powered](https://img.shields.io/badge/AI-Google%20Gemini-purple.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**SmartStudy AI** is a production-grade, AI-powered study planner and personalized learning companion. It empowers students to conquer academic workloads through deterministic multi-factor scheduling, interleaving study sessions, intelligent weak topic detection with rationale explanations, automatic missed-session rescheduling, and contextual AI tutoring via Google Gemini.

---

## ✨ Key Features

### 1. 🔐 Robust User Authentication & Isolation
- User registration and login with cryptographically secure **PBKDF2-HMAC-SHA256** salted password hashing.
- Complete data isolation: every student accesses only their own subjects, topics, schedules, documents, and chat histories.
- Persistent user profiles with preferred daily study hours, preferred study time windows, and degree programs.

### 2. 📚 Subject & Topic Curriculum Management
- Full CRUD management of subjects with custom color tags.
- Detailed topic profiling:
  - **Difficulty:** Easy / Medium / Hard
  - **Priority:** Low / Medium / High
  - **Knowledge Level:** Beginner / Intermediate / Advanced
  - **Status:** Not Started / In Progress / Completed
  - Estimated study hours & optional exam deadlines.

### 3. 📅 Deterministic Time-Slot-Based Scheduling
- Generates **actual clock time slots** (e.g. `06:00 PM - 06:45 PM`) rather than abstract lists.
- Balances exam urgency, topic difficulty, priority, and knowledge deficit.
- **Cognitive Interleaving:** Alternates subjects across slots to prevent mental burnout and improve recall retention.

### 4. 🔄 Smart Missed Session Handling & Auto-Rescheduling
- Detects overdue planned study sessions automatically.
- Re-inserts unfinished topics into the next optimal available slots without exceeding the daily study capacity.
- Displays friendly reschedule notifications allowing students to review schedule adjustments.

### 5. 📊 Visual Progress Analytics & Weak Topic Detection
- Interactive KPI cards: Overall Completion %, Invested Study Hours, Study Streak (consecutive active days), and Exam Countdowns.
- Theme-adaptive visual charts: Donut progress chart, horizontal subject completion bars, and difficulty/priority distribution.
- **Intelligent Weak Topic Detection:** Analyzes multi-factor heuristics and explains *why* a topic is flagged (e.g. `⚠️ Python - Inheritance — Reason: Hard topic + Beginner level + missed 1 session`).
- Displays **Strong Mastered Topics** to celebrate student achievements.

### 6. 🤖 Context-Aware AI Study Assistant (Google Gemini)
- Integrated with Google Gemini models with multi-mode tutoring:
  - **Simple Mode:** ELI5, intuitive analogies, student-friendly language.
  - **Teacher Mode:** Step-by-step curriculum breakdowns, examples, and comprehension check questions.
  - **Exam Mode:** High-yield definitions, scoring keywords, short notes, and practice exam questions.
- **Context Injection:** Seamlessly feeds the student's enrolled subjects, weak topics, and upcoming exam dates into the AI prompt.
- **Graceful Offline Fallback:** Operates seamlessly even if no Google API key is configured.
- Persistent chat history stored in SQLite.

### 7. 📄 Study Material Processing & Semantic Document Q&A
- Supports **PDF**, **DOCX**, **TXT**, and **Images**.
- Scikit-learn **TF-IDF semantic chunking and retrieval** ensures fast, zero-dependency document queries.
- Instant Document Summaries and Practice Exam Question Generators.

### 8. 🎨 Modern AI Dashboard UI/UX
- Responsive card-based layout with rounded corners, subtle shadows, and status badges.
- One-click **Light Mode ☀️ / Dark Mode 🌙** toggle.
- 1-click **Sample Curriculum Loader** for instant testing and demonstration.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.11.9+ | Clean, modular Python code |
| **Frontend UI** | Streamlit >= 1.40 | Interactive web interface with custom CSS |
| **Database ORM** | SQLAlchemy >= 2.0 | SQLite persistent relational database |
| **AI Integration**| Google GenAI / Gemini | Multi-mode conversational tutoring |
| **Analytics** | Scikit-learn, Pandas, NumPy | TF-IDF retrieval, multi-factor scoring |
| **Data Viz** | Matplotlib, Seaborn | Theme-aware responsive charts |
| **Document OCR** | PyPDF, python-docx, Pillow | Multi-format text extraction |

---

## 📁 Project Structure

```
Smartstudy AI/
├── app.py                      # Main Streamlit application and page router
├── requirements.txt            # Project dependencies
├── .env.example                # Template for environment variables
├── .env                        # Local environment configuration
├── README.md                   # Comprehensive documentation
│
├── database/                   # Persistent Database Layer
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models (User, Subject, Topic, etc.)
│   └── db.py                   # Engine, sessionmaker, and DB lifecycle
│
├── auth/                       # Security & User Management
│   ├── __init__.py
│   └── authentication.py       # PBKDF2 password hashing & session management
│
├── planner/                    # Smart Scheduling Engine
│   ├── __init__.py
│   └── scheduler.py            # Time-slot allocation & auto-rescheduling
│
├── analytics/                  # Progress & Weak Topic Engine
│   ├── __init__.py
│   └── progress.py             # Streaks, completion metrics, and weak topic heuristics
│
├── ai/                         # AI Tutoring & Coaching
│   ├── __init__.py
│   ├── chatbot.py              # Multi-mode Gemini assistant & persistent chat
│   ├── planner_ai.py           # Revision advice & personalized study tips
│   └── document_qa.py          # Document Q&A and exam question generator
│
├── documents/                  # Study Material Processing
│   ├── __init__.py
│   └── processor.py            # File text extraction & TF-IDF semantic chunking
│
├── components/                 # Modern UI & Visualization
│   ├── __init__.py
│   ├── ui.py                   # Theme management, CSS injection, badges, KPI cards
│   ├── charts.py               # Matplotlib & Seaborn visual analytics
│   └── dashboard.py            # Dashboard view, daily schedule, and demo seeding
│
└── data/                       # Local SQLite storage
    └── smartstudy.db           # Persistent SQLite database (auto-created)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11.9 or higher installed.

### 2. Clone and Setup Virtual Environment
```bash
# Clone or navigate to the project directory
cd "Smartstudy AI"

# Create virtual environment
python -m venv venv

# Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your **Google Gemini API Key**:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///data/smartstudy.db
```
> **Note:** A Google API key is free and takes 30 seconds to generate at [Google AI Studio](https://aistudio.google.com/). If omitted, SmartStudy AI automatically switches to intelligent offline mode without crashing!

### 5. Run the Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 📖 Example Workflow

1. **Sign In or Quick Demo:**
   - Click **"Launch Demo Student Experience 🚀"** on the login page to immediately explore pre-populated subjects and topics, or create your own custom account.
2. **Review Curriculum:**
   - Open **Subjects & Topics** to view, add, or customize subjects (e.g., Computer Science, Discrete Math, DBMS) with priority and difficulty rankings.
3. **Generate Balanced Schedule:**
   - Navigate to **Study Planner**, select your daily study target (e.g. 3 hours, Evening preset), and click **"Generate Balanced Time-Slot Schedule"**.
   - Notice how subjects are interleaved across 45-minute slots with Pomodoro breaks!
4. **Complete or Reschedule:**
   - Click **"Mark Completed ✓"** on any session to record progress and build your study streak.
   - If an overdue session is missed, SmartStudy automatically moves the topic into the nearest available open slot.
5. **Analyze Progress & Weak Topics:**
   - Head to **Progress & Analytics** to see donut charts, subject completion percentages, and the **"Topics Needing Revision"** section explaining why specific topics are flagged.
6. **Ask the AI Study Assistant:**
   - Switch to **Ask AI Assistant**, choose between **Simple**, **Teacher**, or **Exam** modes, and ask questions. Observe how the AI personalizes answers using your actual subjects and weak topics!
7. **Upload Study Materials:**
   - In **Study Materials**, upload a PDF notes file, click **"Summarize Document"** or **"Generate Practice Exam Questions"** to test your knowledge!

---

## 🔒 Security Best Practices
- **Password Protection:** PBKDF2-HMAC-SHA256 with cryptographically generated 16-byte random salts.
- **SQL Injection Prevention:** 100% parameterized queries via SQLAlchemy ORM.
- **Multi-Tenant Data Isolation:** Every query strictly scopes records to the active `user_id`.
- **Secret Protection:** API keys stored via `.env` or session memory, never checked into version control.

---

## 🔮 Future Improvements
- Spaced repetition algorithm (SM-2) integration for flashcard decks.
- Calendar sync export (`.ics` / Google Calendar integration).
- Voice interaction for audio-guided study sessions.
- Multi-user collaborative study groups and peer benchmarking.
