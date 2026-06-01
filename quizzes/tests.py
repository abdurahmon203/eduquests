from django.test import RequestFactory, TestCase

from levels.models import Level
from subjects.models import Subject

from .models import Question
from .utils import (
    clear_attempt_questions,
    get_all_level_questions,
    load_attempt_questions,
    parse_question_count,
    select_questions_for_attempt,
    store_attempt_questions,
)


class QuizRandomizationTests(TestCase):
    def setUp(self):
        subject = Subject.objects.create(name="Math", description="Numbers")
        self.level = Level.objects.create(
            subject=subject,
            title="Basics",
            description="Intro",
            level_number=1,
        )
        for i in range(6):
            Question.objects.create(
                level=self.level,
                question=f"Q{i}",
                option_a="a",
                option_b="b",
                option_c="c",
                option_d="d",
                correct_answer="A",
            )

    def test_default_returns_all_questions(self):
        selected = select_questions_for_attempt(self.level)
        self.assertEqual(len(selected), 6)

    def test_get_all_level_questions(self):
        self.assertEqual(len(get_all_level_questions(self.level)), 6)

    def test_count_limits_session_subset(self):
        selected = select_questions_for_attempt(self.level, count=2)
        self.assertEqual(len(selected), 2)

    def test_parse_question_count(self):
        factory = RequestFactory()
        self.assertIsNone(parse_question_count(factory.get("/quiz/1/")))
        self.assertIsNone(parse_question_count(factory.get("/quiz/1/?count=all")))
        self.assertEqual(parse_question_count(factory.get("/quiz/1/?count=10")), 10)

    def test_session_round_trip_preserves_question_set(self):
        selected = select_questions_for_attempt(self.level)
        session = {}
        store_attempt_questions(session, self.level.id, selected)
        loaded = load_attempt_questions(session, self.level)
        self.assertEqual([q.id for q in loaded], [q.id for q in selected])

    def test_clear_removes_session_key(self):
        session = {}
        qs = list(Question.objects.filter(level=self.level)[:2])
        store_attempt_questions(session, self.level.id, qs)
        clear_attempt_questions(session, self.level.id)
        self.assertEqual(load_attempt_questions(session, self.level), [])


class GeminiServiceTests(TestCase):
    def test_cheating_request_detected(self):
        from ai_tutor.services.gemini_service import is_cheating_request

        self.assertTrue(is_cheating_request("Give me the direct answer for my final exam"))
        self.assertTrue(is_cheating_request("What is the correct answer for this quiz?"))
        self.assertFalse(is_cheating_request("What is photosynthesis?"))

    def test_cheating_returns_refusal_without_api(self):
        from ai_tutor.services.gemini_service import (
            REFUSAL_MESSAGE,
            generate_tutor_response,
        )

        answer, source = generate_tutor_response("Give me the test answer please")
        self.assertEqual(answer, REFUSAL_MESSAGE)
        self.assertEqual(source, "gemini")
