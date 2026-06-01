from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import TutorQuestion, TutorResponse


class AskEndpointTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student",
            email="student@test.com",
            password="pass12345",
        )
        self.client = Client()
        self.client.login(username="student", password="pass12345")

    def test_ask_requires_question(self):
        resp = self.client.post(
            reverse("ai_ask"),
            data='{"question": "", "subject": "", "level": ""}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_ask_saves_tutor_records_on_cheating_request(self):
        resp = self.client.post(
            reverse("ai_ask"),
            data='{"question": "Give me the exam answer", "subject": "Bio", "level": "1"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("help you understand", data["answer"].lower())
        self.assertIn("source", data)
        self.assertEqual(TutorQuestion.objects.filter(user=self.user).count(), 1)
        tq = TutorQuestion.objects.get(user=self.user)
        self.assertEqual(tq.subject, "Bio")
        self.assertTrue(hasattr(tq, "ai_response"))
        self.assertEqual(TutorResponse.objects.count(), 1)
