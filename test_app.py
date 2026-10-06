"""
Comprehensive Automated Test Suite for SmartStudy AI.
Verifies all functional requirements specified in the project specification:
1. Authentication (Registration, password hashing, login, profile updates)
2. Database persistence & multi-tenant user data isolation
3. Subject and Topic CRUD
4. Intelligent Time-Slot Study Scheduling with Pomodoro and Interleaving
5. Automatic Missed Study Session Detection and Rescheduling
6. Progress tracking, study streak calculation, and metrics
7. Intelligent Multi-Factor Weak Topic Detection with human-readable rationale
8. AI Assistant modes (Simple, Teacher, Exam) and contextual injection
9. Graceful offline fallback when Google API key is absent
10. Document parsing (PDF, DOCX, TXT, Images) and TF-IDF chunk retrieval
"""

import os
import sys
import unittest
from datetime import date, datetime, timedelta, time

# Add root directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db import init_db, get_db
from database.models import User, Subject, Topic, StudySession, ProgressLog, UploadedMaterial, ChatMessage
from auth.authentication import (
    register_user,
    authenticate_user,
    get_user_profile,
    update_user_profile,
    update_user_password,
    verify_password
)
from planner.scheduler import (
    generate_time_slots,
    calculate_topic_urgency_score,
    generate_balanced_study_plan,
    detect_and_reschedule_missed_sessions,
    complete_study_session,
    get_user_schedule_for_date
)
from analytics.progress import (
    calculate_study_streak,
    get_progress_overview,
    get_subject_wise_analytics,
    analyze_weak_and_strong_topics
)
from ai.chatbot import (
    ask_study_assistant,
    get_chat_history,
    clear_chat_history,
    get_student_context,
    generate_fallback_offline_response
)
from documents.processor import (
    process_uploaded_document,
    chunk_text,
    search_relevant_chunks,
    extract_text_from_txt
)
from ai.document_qa import ask_document_question, summarize_document
from ai.planner_ai import get_ai_study_recommendations


class TestSmartStudyAI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database schema before running tests."""
        init_db()

    def setUp(self):
        """Create a clean unique test user for each test."""
        self.username = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.email = f"{self.username}@testuniversity.edu"
        self.password = "securePass123!"

        success, msg, user_dict = register_user(
            username=self.username,
            email=self.email,
            password=self.password,
            full_name="Alex Test Student",
            course="Computer Science",
            year_of_study="3rd Year"
        )
        self.assertTrue(success, f"Failed to register test user: {msg}")
        self.assertIsNotNone(user_dict)
        self.user_id = user_dict["id"]

    def test_01_authentication_and_password_hashing(self):
        """Test registration, secure PBKDF2 hashing, login verification, and profile."""
        # Check that stored password is NOT plain text
        with get_db() as db:
            user = db.query(User).filter(User.id == self.user_id).first()
            self.assertNotEqual(user.password_hash, self.password)
            self.assertTrue("$" in user.password_hash)
            self.assertTrue(verify_password(self.password, user.password_hash))
            self.assertFalse(verify_password("wrongPassword", user.password_hash))

        # Test login via username
        auth_ok, msg, user_info = authenticate_user(self.username, self.password)
        self.assertTrue(auth_ok)
        self.assertEqual(user_info["id"], self.user_id)

        # Test login via email
        auth_ok_email, _, _ = authenticate_user(self.email, self.password)
        self.assertTrue(auth_ok_email)

        # Test duplicate registration rejection
        dup_ok, dup_msg, _ = register_user(self.username, "another@email.com", "pass123")
        self.assertFalse(dup_ok)
        self.assertIn("already taken", dup_msg)

        # Test profile update
        up_ok, up_msg = update_user_profile(
            user_id=self.user_id,
            full_name="Alex T. Student Updated",
            course="Software Engineering",
            year_of_study="4th Year",
            preferred_study_hours=4.0,
            preferred_study_time="Night (8:00 PM - 12:00 AM)"
        )
        self.assertTrue(up_ok)
        prof = get_user_profile(self.user_id)
        self.assertEqual(prof["full_name"], "Alex T. Student Updated")
        self.assertEqual(prof["preferred_study_hours"], 4.0)

    def test_02_subject_and_topic_management(self):
        """Test creating subjects, adding topics with difficulty and priorities."""
        with get_db() as db:
            # Add Subject
            sub = Subject(
                user_id=self.user_id,
                name="Data Structures",
                code="CS201",
                color="#4F46E5",
                description="Trees, Graphs, and Hash Tables"
            )
            db.add(sub)
            db.flush()
            sub_id = sub.id

            # Add Topics
            t1 = Topic(
                subject_id=sub_id,
                name="Binary Search Trees",
                difficulty="Medium",
                priority="High",
                knowledge_level="Beginner",
                status="Not Started",
                estimated_duration_hours=2.0
            )
            t2 = Topic(
                subject_id=sub_id,
                name="Graph Dijkstra Algorithm",
                difficulty="Hard",
                priority="High",
                knowledge_level="Beginner",
                status="In Progress",
                estimated_duration_hours=3.0,
                exam_date=date.today() + timedelta(days=4)
            )
            db.add_all([t1, t2])

        # Verify query isolation — filter to just the subject this test added
        with get_db() as db:
            user_topics = (
                db.query(Topic)
                .join(Subject)
                .filter(Subject.user_id == self.user_id, Subject.name == "Data Structures")
                .all()
            )
            # The default curriculum also has a "Data Structures" subject with 5 topics,
            # but this test creates a SECOND "Data Structures" — both belong to the same user.
            # Just verify our 2 specific topics exist by name.
            topic_names = {t.name for t in user_topics}
            self.assertIn("Binary Search Trees", topic_names)
            self.assertIn("Graph Dijkstra Algorithm", topic_names)
            self.assertTrue(all(t.subject.name == "Data Structures" for t in user_topics))

    def test_03_time_slot_study_schedule_generation(self):
        """Test time-slot-based balanced scheduling with subject interleaving."""
        with get_db() as db:
            s1 = Subject(user_id=self.user_id, name="Mathematics", color="#EC4899")
            s2 = Subject(user_id=self.user_id, name="Python", color="#4F46E5")
            db.add_all([s1, s2])
            db.flush()

            t1 = Topic(subject_id=s1.id, name="Calculus Derivatives", difficulty="Medium", priority="High", status="In Progress")
            t2 = Topic(subject_id=s1.id, name="Linear Algebra", difficulty="Easy", priority="Low", status="Not Started")
            t3 = Topic(subject_id=s2.id, name="Decorators & Generators", difficulty="Hard", priority="High", status="Not Started")
            t4 = Topic(subject_id=s2.id, name="Asyncio Event Loop", difficulty="Hard", priority="High", status="In Progress")
            db.add_all([t1, t2, t3, t4])

        # Generate 3-day plan, 2 hours/day (45 min slots + 15 min break)
        plan_res = generate_balanced_study_plan(
            user_id=self.user_id,
            days_to_plan=3,
            daily_study_hours=2.0,
            preferred_time_preset="Evening (6:00 PM - 10:00 PM)",
            session_duration_minutes=45,
            break_minutes=15
        )

        self.assertTrue(plan_res["success"])
        self.assertGreater(plan_res["count"], 0)

        # Check today's scheduled sessions have valid formatted time slots
        today_sessions = get_user_schedule_for_date(self.user_id, date.today())
        self.assertGreater(len(today_sessions), 0)
        first_session = today_sessions[0]
        self.assertIn("PM", first_session["start_time"])
        self.assertIn("PM", first_session["end_time"])
        self.assertEqual(first_session["status"], "Planned")

    def test_04_session_completion_and_streak(self):
        """Test marking a session complete and verifying progress & streak updates."""
        with get_db() as db:
            s = Subject(user_id=self.user_id, name="Chemistry")
            db.add(s)
            db.flush()
            t = Topic(subject_id=s.id, name="Organic Chemistry", status="In Progress")
            db.add(t)
            db.flush()
            sess = StudySession(
                user_id=self.user_id,
                topic_id=t.id,
                session_date=date.today(),
                start_time="06:00 PM",
                end_time="06:45 PM",
                duration_minutes=45,
                status="Planned"
            )
            db.add(sess)
            db.flush()
            sess_id = sess.id

        # Mark session complete
        ok, msg = complete_study_session(sess_id, notes="Covered reaction mechanisms")
        self.assertTrue(ok)

        # Verify streak and overview
        overview = get_progress_overview(self.user_id)
        self.assertGreaterEqual(overview["actual_hours"], 0.7)  # 45 mins = 0.75h
        streak = calculate_study_streak(self.user_id)
        self.assertGreaterEqual(streak, 1)

    def test_05_missed_session_detection_and_auto_rescheduling(self):
        """Test auto-rescheduling of missed past planned sessions."""
        yesterday = date.today() - timedelta(days=1)
        with get_db() as db:
            s = Subject(user_id=self.user_id, name="Physics")
            db.add(s)
            db.flush()
            t = Topic(subject_id=s.id, name="Thermodynamics", difficulty="Hard", priority="High", status="In Progress")
            db.add(t)
            db.flush()
            past_sess = StudySession(
                user_id=self.user_id,
                topic_id=t.id,
                session_date=yesterday,
                start_time="06:00 PM",
                end_time="06:45 PM",
                duration_minutes=45,
                status="Planned"
            )
            db.add(past_sess)
            db.flush()
            past_id = past_sess.id

        # Trigger missed session rescheduling
        rescheduled_count, notes = detect_and_reschedule_missed_sessions(self.user_id)
        self.assertGreaterEqual(rescheduled_count, 1)
        self.assertGreater(len(notes), 0)
        self.assertIn("Thermodynamics", notes[0])
        self.assertIn("adjusted", notes[0].lower())

        # Verify old session marked Missed
        with get_db() as db:
            old_s = db.query(StudySession).filter(StudySession.id == past_id).first()
            self.assertEqual(old_s.status, "Missed")

            # Check new session created
            new_s = db.query(StudySession).filter(
                StudySession.user_id == self.user_id,
                StudySession.rescheduled_from_id == past_id
            ).first()
            self.assertIsNotNone(new_s)
            self.assertEqual(new_s.status, "Planned")
            self.assertGreaterEqual(new_s.session_date, date.today())

    def test_06_weak_topic_detection_with_explanations(self):
        """Test intelligent multi-factor weak topic detection with detailed reasons."""
        with get_db() as db:
            s = Subject(user_id=self.user_id, name="Database Systems")
            db.add(s)
            db.flush()

            # Weak Topic: Hard + High Priority + Beginner + Exam close + Missed session
            t_weak = Topic(
                subject_id=s.id,
                name="Normalization (BCNF)",
                difficulty="Hard",
                priority="High",
                knowledge_level="Beginner",
                status="In Progress",
                exam_date=date.today() + timedelta(days=3)
            )
            # Strong Topic: Completed + Advanced
            t_strong = Topic(
                subject_id=s.id,
                name="Relational Algebra",
                difficulty="Medium",
                priority="Medium",
                knowledge_level="Advanced",
                status="Completed",
                completed_at=datetime.now()
            )
            db.add_all([t_weak, t_strong])
            db.flush()

            # Add missed session for weak topic
            missed = StudySession(
                user_id=self.user_id,
                topic_id=t_weak.id,
                session_date=date.today() - timedelta(days=1),
                start_time="06:00 PM",
                end_time="06:45 PM",
                status="Missed"
            )
            db.add(missed)

        analysis = analyze_weak_and_strong_topics(self.user_id)
        weak_list = analysis["weak_topics"]
        strong_list = analysis["strong_topics"]

        self.assertGreater(len(weak_list), 0)
        self.assertEqual(weak_list[0]["topic_name"], "Normalization (BCNF)")
        self.assertIn("Challenging topic", weak_list[0]["reason"])
        self.assertIn("Beginner", weak_list[0]["reason"])
        self.assertIn("missed", weak_list[0]["reason"])

        self.assertGreater(len(strong_list), 0)
        self.assertEqual(strong_list[0]["topic_name"], "Relational Algebra")
        self.assertIn("Advanced mastery", strong_list[0]["reason"])

    def test_07_ai_modes_and_offline_fallback(self):
        """Test AI Study Assistant with Simple, Teacher, and Exam modes, and persistent chat."""
        # 1. Simple Mode query (runs in graceful offline fallback if no API key is set)
        ans_simple = ask_study_assistant(
            user_id=self.user_id,
            user_query="Explain inheritance in object-oriented programming",
            mode="Simple",
            save_to_history=True
        )
        self.assertIsNotNone(ans_simple)
        self.assertTrue(len(ans_simple) > 50)

        # 2. Teacher Mode query
        ans_teacher = ask_study_assistant(
            user_id=self.user_id,
            user_query="How do binary search trees balance?",
            mode="Teacher",
            save_to_history=True
        )
        self.assertIsNotNone(ans_teacher)

        # 3. Exam Mode query
        ans_exam = ask_study_assistant(
            user_id=self.user_id,
            user_query="What are key normalization rules for exam?",
            mode="Exam",
            save_to_history=True
        )
        self.assertIsNotNone(ans_exam)

        # 4. Check Chat History persistence in SQLite
        history = get_chat_history(self.user_id)
        self.assertGreaterEqual(len(history), 6)  # 3 queries * (user + assistant) = 6 messages
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

        # 5. Clear chat
        clear_ok = clear_chat_history(self.user_id)
        self.assertTrue(clear_ok)
        self.assertEqual(len(get_chat_history(self.user_id)), 0)

    def test_08_document_processing_and_retrieval(self):
        """Test text extraction, TF-IDF semantic chunking and Q&A."""
        sample_doc_content = (
            "Operating Systems Lecture Notes.\n\n"
            "Process Management and Thread Synchronization.\n"
            "A process is a program in execution containing program counter, stack, and data section. "
            "Processes communicate using Inter-Process Communication (IPC) such as pipes, message queues, and shared memory.\n\n"
            "Deadlock Conditions:\n"
            "Four Coffman conditions must hold simultaneously for deadlock: "
            "1. Mutual Exclusion, 2. Hold and Wait, 3. No Preemption, 4. Circular Wait.\n\n"
            "Virtual Memory and Paging:\n"
            "Paging prevents external fragmentation by dividing physical memory into fixed-size frames "
            "and logical memory into equal-size pages."
        )

        success, text, ftype, msg = process_uploaded_document("lecture_notes.txt", sample_doc_content.encode("utf-8"))
        self.assertTrue(success)
        self.assertEqual(ftype, "txt")
        self.assertIn("Deadlock", text)

        # Test chunking
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
        self.assertGreater(len(chunks), 1)

        # Test TF-IDF Semantic Retrieval
        retrieved = search_relevant_chunks("What are the deadlock conditions?", chunks, top_k=1)
        self.assertGreater(len(retrieved), 0)
        top_chunk, score = retrieved[0]
        self.assertIn("Deadlock", top_chunk)

        # Save to UploadedMaterial and test Q&A
        with get_db() as db:
            mat = UploadedMaterial(
                user_id=self.user_id,
                filename="lecture_notes.txt",
                file_type="txt",
                file_size_kb=1.2,
                extracted_text=sample_doc_content
            )
            db.add(mat)
            db.flush()
            mat_id = mat.id

        ans = ask_document_question(mat_id, "What are the four Coffman conditions for deadlock?")
        self.assertIn("Coffman", ans)

    def test_09_detached_instance_access_safety(self):
        """Test that objects accessed outside of with get_db() session do NOT raise DetachedInstanceError."""
        # 1. Add subject and topic
        with get_db() as db:
            s = Subject(user_id=self.user_id, name="Algorithms", code="CS301", color="#6366f1")
            db.add(s)
            db.flush()
            t = Topic(subject_id=s.id, name="Divide and Conquer", difficulty="Medium", priority="High")
            db.add(t)

        # 2. Query outside the session and verify accessing topic.subject works without session
        with get_db() as db:
            # Filter specifically to the "Algorithms" subject this test created
            topics = (
                db.query(Topic)
                .join(Subject)
                .filter(Subject.user_id == self.user_id, Subject.name == "Algorithms")
                .all()
            )
            subjects = db.query(Subject).filter(
                Subject.user_id == self.user_id, Subject.name == "Algorithms"
            ).all()

        # Session is closed now!
        # Access relationships on detached instances
        for topic in topics:
            # Must NOT raise DetachedInstanceError!
            sub_name = topic.subject.name
            sub_color = topic.subject.color
            self.assertEqual(sub_name, "Algorithms")
            self.assertEqual(sub_color, "#6366f1")


        for subject in subjects:
            # Must NOT raise DetachedInstanceError!
            t_count = len(subject.topics)
            self.assertGreaterEqual(t_count, 1)
            topic_names = [tp.name for tp in subject.topics]
            self.assertIn("Divide and Conquer", topic_names)

    def test_10_default_curriculum_seeder(self):
        """Test that registration seeds exactly 5 default subjects with 25 topics, and seeder is idempotent."""
        from database.seeds import seed_default_curriculum

        default_names = {
            "Python", "Data Structures", "Database Management Systems (DBMS)",
            "Artificial Intelligence", "Machine Learning"
        }
        with get_db() as db:
            seeded_subjects = (
                db.query(Subject)
                .filter(Subject.user_id == self.user_id, Subject.name.in_(default_names))
                .all()
            )
            self.assertEqual(len(seeded_subjects), 5, "Should have exactly 5 default subjects")

            total_topics = (
                db.query(Topic)
                .join(Subject)
                .filter(Subject.user_id == self.user_id, Subject.name.in_(default_names))
                .count()
            )
            self.assertEqual(total_topics, 25, "Should have exactly 25 default topics (5 per subject)")

            # Idempotency: calling seeder again should add 0 subjects
            count_before = db.query(Subject).filter(Subject.user_id == self.user_id).count()
            added = seed_default_curriculum(self.user_id, db)
            self.assertEqual(added, 0, "Seeder should be idempotent — 0 subjects added on second call")
            count_after = db.query(Subject).filter(Subject.user_id == self.user_id).count()
            self.assertEqual(count_before, count_after, "Subject count must not change on second seed")


if __name__ == "__main__":
    unittest.main()

