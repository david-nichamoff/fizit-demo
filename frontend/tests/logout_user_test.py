import logging
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth import get_user
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

from frontend.views.dashboard import DashboardLogoutView

class DashboardLogoutViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.logout_url = reverse("dashboard_logout")
        self.login_url = reverse("dashboard_login")
        self.user = User.objects.create_user(username="fizit", password="fizitpass")

    def test_authenticated_user_logout(self):
        request = self.factory.get(self.logout_url)
        request.user = self.user
        request.session = self.client.session  # mock session for flush()

        response = DashboardLogoutView.as_view()(request)

        # Ensure user was redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.login_url)

    def test_unauthenticated_user_logout(self):
        request = self.factory.get(self.logout_url)
        request.user = AnonymousUser()
        request.session = self.client.session

        response = DashboardLogoutView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.login_url)