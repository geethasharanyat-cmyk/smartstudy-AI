"""
Default curriculum seeder for SmartStudy AI.
Creates 5 mandatory subjects with their topics for every newly registered student.
This function is idempotent — safe to call multiple times.
"""

from database.models import Subject, Topic


# ---------------------------------------------------------------------------
# Default curriculum definition
# ---------------------------------------------------------------------------
DEFAULT_CURRICULUM = [
    {
        "name": "Python",
        "code": "PY101",
        "color": "#3B82F6",
        "description": "Programming fundamentals using Python",
        "topics": [
            {"name": "Variables and Data Types",  "difficulty": "Easy",   "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Functions",                  "difficulty": "Easy",   "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 2.0},
            {"name": "Object-Oriented Programming","difficulty": "Medium", "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 3.0},
            {"name": "Inheritance",                "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 2.0},
            {"name": "Exception Handling",         "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 1.5},
        ],
    },
    {
        "name": "Data Structures",
        "code": "DS201",
        "color": "#10B981",
        "description": "Fundamental data structures and algorithms",
        "topics": [
            {"name": "Arrays",        "difficulty": "Easy",   "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Linked Lists",  "difficulty": "Medium", "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 2.0},
            {"name": "Stacks",        "difficulty": "Easy",   "priority": "Medium", "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Queues",        "difficulty": "Easy",   "priority": "Medium", "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Trees",         "difficulty": "Hard",   "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 3.0},
        ],
    },
    {
        "name": "Database Management Systems (DBMS)",
        "code": "DBMS301",
        "color": "#F59E0B",
        "description": "Relational databases, SQL, and data modelling",
        "topics": [
            {"name": "ER Model",       "difficulty": "Easy",   "priority": "Medium", "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "SQL",            "difficulty": "Medium", "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 3.0},
            {"name": "Normalization",  "difficulty": "Hard",   "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 2.5},
            {"name": "Transactions",   "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 2.0},
            {"name": "Indexing",       "difficulty": "Hard",   "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 2.0},
        ],
    },
    {
        "name": "Artificial Intelligence",
        "code": "AI401",
        "color": "#8B5CF6",
        "description": "Core concepts, search algorithms, and AI applications",
        "topics": [
            {"name": "Introduction to AI",         "difficulty": "Easy",   "priority": "Medium", "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Intelligent Agents",         "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Beginner",     "estimated_duration_hours": 2.0},
            {"name": "Search Algorithms",          "difficulty": "Hard",   "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 3.0},
            {"name": "Knowledge Representation",   "difficulty": "Hard",   "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 2.5},
            {"name": "AI Applications",            "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 2.0},
        ],
    },
    {
        "name": "Machine Learning",
        "code": "ML501",
        "color": "#EF4444",
        "description": "Supervised and unsupervised learning algorithms",
        "topics": [
            {"name": "Introduction to Machine Learning", "difficulty": "Easy",   "priority": "High",   "knowledge_level": "Beginner",     "estimated_duration_hours": 1.5},
            {"name": "Regression",                       "difficulty": "Medium", "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 2.5},
            {"name": "Classification",                   "difficulty": "Medium", "priority": "High",   "knowledge_level": "Intermediate", "estimated_duration_hours": 2.5},
            {"name": "Clustering",                       "difficulty": "Medium", "priority": "Medium", "knowledge_level": "Intermediate", "estimated_duration_hours": 2.0},
            {"name": "Model Evaluation",                 "difficulty": "Hard",   "priority": "High",   "knowledge_level": "Advanced",     "estimated_duration_hours": 2.0},
        ],
    },
]


def seed_default_curriculum(user_id: int, db) -> int:
    """
    Creates the default 5 subjects and their topics for a newly registered student.

    Parameters
    ----------
    user_id : int
        The primary key of the newly created User row.
    db : Session
        An open SQLAlchemy session (caller manages the session lifecycle).

    Returns
    -------
    int
        Number of subjects created (0 if the user already had subjects).
    """
    # Idempotency guard — do not re-seed if subjects already exist
    existing_count = db.query(Subject).filter(Subject.user_id == user_id).count()
    if existing_count > 0:
        return 0

    subjects_created = 0
    for subject_data in DEFAULT_CURRICULUM:
        subject = Subject(
            user_id=user_id,
            name=subject_data["name"],
            code=subject_data["code"],
            color=subject_data["color"],
            description=subject_data["description"],
        )
        db.add(subject)
        db.flush()  # populate subject.id before adding topics

        for topic_data in subject_data["topics"]:
            topic = Topic(
                subject_id=subject.id,
                name=topic_data["name"],
                difficulty=topic_data["difficulty"],
                priority=topic_data["priority"],
                knowledge_level=topic_data["knowledge_level"],
                status="Not Started",
                estimated_duration_hours=topic_data["estimated_duration_hours"],
            )
            db.add(topic)

        subjects_created += 1

    return subjects_created
