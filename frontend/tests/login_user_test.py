from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.models import User, Group

from frontend.views.dashboard import DashboardLoginView

class DashboardLoginViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.login_url = reverse("dashboard_login")
        self.user = User.objects.create_user(username="fizit", password="fizitpass")

        # ✅ Add user to the 'fizit' group
        fizit_group, _ = Group.objects.get_or_create(name="fizit")
        self.user.groups.add(fizit_group)

    def test_get_login_page_renders_successfully(self):
        request = self.factory.get(self.login_url, {"next": "/dashboard/fizit/"})
        request.user = AnonymousUser()
        response = DashboardLoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_login_redirects_to_safe_next_url(self):
        self.client.login(username="fizit", password="fizitpass")
        response = self.client.post(
            self.login_url,
            {"username": "fizit", "password": "fizitpass", "next": "/dashboard/fizit/"},
            follow=True
        )
        self.assertRedirects(response, "/dashboard/fizit/")

    def test_login_redirects_to_default_when_next_is_unsafe(self):
        self.client.login(username="fizit", password="fizitpass")
        response = self.client.post(
            self.login_url,
            {"username": "fizit", "password": "fizitpass", "next": "http://malicious.com"},
            follow=True
        )
        self.assertRedirects(response, reverse("list_contracts", kwargs={"customer": "fizit"}))