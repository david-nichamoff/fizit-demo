from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('dashboard_login')

    def test_get_register_page(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/register.html')
        self.assertIn('form', response.context)

    def test_post_valid_registration(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, data=form_data)
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_post_invalid_registration(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'password123',
            'password2': 'mismatch123',
        }
        response = self.client.post(self.register_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/register.html')

        form = response.context.get("form")
        self.assertTrue(form.errors)
        self.assertIn("password2", form.errors)
        self.assertIn("didn’t match", form.errors["password2"][0])