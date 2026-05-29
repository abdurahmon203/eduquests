from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from .forms import ContactForm

class StaticPagesTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Learn Smarter, Not Harder')
        self.assertContains(response, 'EduQuest helps you reach your goals')

    def test_about_page(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')
        self.assertContains(response, 'What is EduQuests?')
        self.assertContains(response, 'Reimagining educational technology')

    def test_contact_page_get(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')
        self.assertIsInstance(response.context['form'], ContactForm)
        self.assertContains(response, 'Send us a Message')

    def test_contact_page_post_success(self):
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Hello, I have a question about courses.'
        }
        response = self.client.post(reverse('contact'), data=form_data)
        # Should redirect to contact URL
        self.assertRedirects(response, reverse('contact'))
        
        # Verify success message was created
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your message has been sent successfully! We will get back to you shortly.")

    def test_contact_page_post_invalid(self):
        form_data = {
            'name': '',
            'email': 'invalid-email',
            'message': ''
        }
        response = self.client.post(reverse('contact'), data=form_data)
        # Should render contact page again with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')
        
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('message', form.errors)

