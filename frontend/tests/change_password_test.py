from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="fizit", password="oldpassword")
        self.client.login(username="fizit", password="oldpassword")
        self.change_password_url = reverse("change_password")

    def test_get_change_password_page(self):
        response = self.client.get(self.change_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_post_invalid_password_form_errors(self):
        response = self.client.post(self.change_password_url, {
            "old_password": "wrongpassword",
            "new_password1": "newsecurepassword123",
            "new_password2": "newsecurepassword123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("old_password", form.errors)
        self.assertIn("incorrect", form.errors["old_password"][0].lower())

    def test_post_invalid_password_with_django_assert(self):
        response = self.client.post(self.change_password_url, {
            "old_password": "wrongpassword",
            "new_password1": "newsecurepassword123",
            "new_password2": "newsecurepassword123"
        })
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertFormError(
            form, "old_password",
            "Your old password was entered incorrectly. Please enter it again."
        )